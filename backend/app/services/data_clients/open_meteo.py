import asyncio
import logging
from typing import Dict, Any, Tuple
import httpx

from app.config import settings
from app.services.data_clients.base import BaseDataClient

logger = logging.getLogger(__name__)

class OpenMeteoClient(BaseDataClient):
    """
    Client for Open-Meteo Forecast & Soil Moisture API (PRIMARY source).
    Provides 7-day weather forecast, rain sum, wind speed, humidity,
    and multi-depth soil moisture / soil temperature.
    """
    def __init__(self):
        super().__init__(
            ttl_seconds=settings.CACHE_WEATHER_TTL_SEC,
            timeout_seconds=6.0,
            max_retries=2
        )
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        cache_key = self._get_location_key(lat, lon, "open_meteo")
        cached = self.get_cached(cache_key)
        if cached is not None:
            logger.info(f"OpenMeteo cache hit for ({lat}, {lon})")
            return cached, True

        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max"
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "soil_temperature_0_to_7cm",
                "soil_moisture_0_to_7cm",
                "soil_moisture_7_to_28cm"
            ],
            "timezone": "auto",
            "forecast_days": 7
        }

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.get(self.base_url, params=params)
                    if resp.status_code == 200:
                        raw = resp.json()
                        parsed = self._parse_response(raw)
                        self.set_cached(cache_key, parsed)
                        return parsed, True
                    else:
                        logger.warning(f"OpenMeteo returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.warning(f"OpenMeteo attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        logger.error(f"OpenMeteo all attempts failed for ({lat}, {lon}). Falling back to degraded estimates.")
        fallback = self._get_fallback(lat, lon)
        return fallback, False

    def _parse_response(self, raw: dict) -> Dict[str, Any]:
        daily = raw.get("daily", {})
        hourly = raw.get("hourly", {})

        # Extract daily aggregates
        max_temps = daily.get("temperature_2m_max", [30.0])
        min_temps = daily.get("temperature_2m_min", [18.0])
        precip_sums = daily.get("precipitation_sum", [0.0])
        precip_probs = daily.get("precipitation_probability_max", [10.0])
        winds = daily.get("wind_speed_10m_max", [10.0])

        # Current / next 24h & 48h
        forecast_max_temp_c = float(max_temps[0]) if max_temps else 30.0
        forecast_min_temp_c = float(min_temps[0]) if min_temps else 18.0
        forecast_rain_24h_mm = float(precip_sums[0]) if precip_sums else 0.0
        forecast_rain_48h_mm = sum(precip_sums[:2]) if len(precip_sums) >= 2 else forecast_rain_24h_mm
        forecast_rain_7d_mm = sum(precip_sums[:7]) if len(precip_sums) >= 1 else 0.0
        rain_probability_pct = float(precip_probs[0]) if precip_probs else 10.0
        wind_speed_kmh = float(winds[0]) if winds else 10.0

        # Hourly soil & humidity
        soil_m_0_7 = hourly.get("soil_moisture_0_to_7cm", [])
        soil_m_7_28 = hourly.get("soil_moisture_7_to_28cm", [])
        soil_t_0_7 = hourly.get("soil_temperature_0_to_7cm", [])
        humidities = hourly.get("relative_humidity_2m", [])

        # Open-Meteo volumetric soil moisture is m3/m3 (e.g. 0.28). Convert to % (e.g. 28.0%)
        current_sm_0_7 = (float(soil_m_0_7[0]) * 100.0) if soil_m_0_7 and soil_m_0_7[0] is not None else 32.0
        current_sm_7_28 = (float(soil_m_7_28[0]) * 100.0) if soil_m_7_28 and soil_m_7_28[0] is not None else 35.0
        current_st_0_7 = float(soil_t_0_7[0]) if soil_t_0_7 and soil_t_0_7[0] is not None else 26.0
        current_rh = float(humidities[0]) if humidities and humidities[0] is not None else 50.0

        return {
            "source": "Open-Meteo API",
            "forecast_max_temp_c": round(forecast_max_temp_c, 1),
            "forecast_min_temp_c": round(forecast_min_temp_c, 1),
            "forecast_rain_24h_mm": round(forecast_rain_24h_mm, 1),
            "forecast_rain_48h_mm": round(forecast_rain_48h_mm, 1),
            "forecast_rain_7d_mm": round(forecast_rain_7d_mm, 1),
            "rain_probability_pct": round(rain_probability_pct, 1),
            "wind_speed_kmh": round(wind_speed_kmh, 1),
            "relative_humidity_pct": round(current_rh, 1),
            "soil_moisture_0_7cm_pct": round(current_sm_0_7, 1),
            "soil_moisture_7_28cm_pct": round(current_sm_7_28, 1),
            "soil_temp_0_7cm_c": round(current_st_0_7, 1),
            "raw_daily": daily
        }

    def _get_fallback(self, lat: float, lon: float) -> Dict[str, Any]:
        """Climatological seasonal fallback if Open-Meteo is temporarily unreachable."""
        return {
            "source": "Climatological Fallback (Open-Meteo Degraded)",
            "forecast_max_temp_c": 31.0,
            "forecast_min_temp_c": 19.0,
            "forecast_rain_24h_mm": 0.0,
            "forecast_rain_48h_mm": 0.0,
            "forecast_rain_7d_mm": 0.0,
            "rain_probability_pct": 10.0,
            "wind_speed_kmh": 10.0,
            "relative_humidity_pct": 48.0,
            "soil_moisture_0_7cm_pct": 30.0,
            "soil_moisture_7_28cm_pct": 34.0,
            "soil_temp_0_7cm_c": 25.0,
            "raw_daily": {}
        }
