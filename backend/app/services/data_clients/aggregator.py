import asyncio
import logging
from typing import Dict, Any

from app.config import settings
from app.schemas.rules import EnvironmentalSnapshot, DayOutlook
from app.services.data_clients.open_meteo import OpenMeteoClient
from app.services.data_clients.nasa_power import NasaPowerClient
from app.services.data_clients.isric_soilgrids import ISRICSoilGridsClient

logger = logging.getLogger(__name__)

class EnvironmentalAggregator:
    def __init__(self):
        self.open_meteo = OpenMeteoClient()
        self.nasa_power = NasaPowerClient()
        self.soil_grids = ISRICSoilGridsClient()

    async def get_environmental_snapshot(self, lat: float, lon: float, force_mock: bool = False) -> EnvironmentalSnapshot:
        """
        Orchestrate parallel fetches from Open-Meteo, NASA POWER, and ISRIC SoilGrids.
        Gracefully handles partial downtime without failing the pipeline.
        """
        if force_mock or settings.MOCK_DATA:
            return self._build_mock_snapshot(lat, lon)

        # Execute parallel external API requests
        results = await asyncio.gather(
            self.open_meteo.fetch(lat, lon),
            self.nasa_power.fetch(lat, lon),
            self.soil_grids.fetch(lat, lon),
            return_exceptions=True
        )

        om_res, om_ok = results[0] if not isinstance(results[0], Exception) else (self.open_meteo._get_fallback(lat, lon), False)
        np_res, np_ok = results[1] if not isinstance(results[1], Exception) else (self.nasa_power._get_fallback(), False)
        sg_res, sg_ok = results[2] if not isinstance(results[2], Exception) else (self.soil_grids._get_fallback(), False)

        # Determine overall confidence
        sources_used = []
        if om_ok:
            sources_used.append("Open-Meteo")
        else:
            sources_used.append("Open-Meteo (Degraded)")

        if np_ok:
            sources_used.append("NASA POWER")
        else:
            sources_used.append("NASA POWER (Degraded)")

        if sg_ok:
            sources_used.append("ISRIC SoilGrids")
        else:
            sources_used.append("ISRIC SoilGrids (Baseline)")

        if om_ok and np_ok and sg_ok:
            data_confidence = "HIGH"
        elif om_ok:
            data_confidence = "MEDIUM"
        else:
            data_confidence = "LOW"

        return EnvironmentalSnapshot(
            latitude=round(lat, 4),
            longitude=round(lon, 4),
            forecast_max_temp_c=om_res["forecast_max_temp_c"],
            forecast_min_temp_c=om_res["forecast_min_temp_c"],
            forecast_rain_24h_mm=om_res["forecast_rain_24h_mm"],
            forecast_rain_48h_mm=om_res["forecast_rain_48h_mm"],
            forecast_rain_7d_mm=om_res["forecast_rain_7d_mm"],
            rain_probability_pct=om_res["rain_probability_pct"],
            wind_speed_kmh=om_res["wind_speed_kmh"],
            relative_humidity_pct=om_res["relative_humidity_pct"],
            soil_moisture_0_7cm_pct=om_res["soil_moisture_0_7cm_pct"],
            soil_moisture_7_28cm_pct=om_res["soil_moisture_7_28cm_pct"],
            soil_temp_0_7cm_c=om_res["soil_temp_0_7cm_c"],
            soil_texture_class=sg_res["soil_texture_class"],
            consecutive_dry_days=np_res["consecutive_dry_days"],
            cumulative_rain_30d_mm=np_res["cumulative_rain_30d_mm"],
            daily_outlook=self._daily_outlook(om_res.get("raw_daily") or {}),
            data_confidence=data_confidence,
            sources_used=sources_used
        )

    @staticmethod
    def _daily_outlook(daily: dict, days: int = 5) -> list:
        """Turn Open-Meteo's parallel daily arrays into per-day records; empty if the data is missing."""
        dates = daily.get("time") or []
        def col(name, default):
            values = daily.get(name) or []
            return [default if v is None else v for v in values]
        rain, prob = col("precipitation_sum", 0.0), col("precipitation_probability_max", 0.0)
        tmax, tmin, wind = col("temperature_2m_max", 0.0), col("temperature_2m_min", 0.0), col("wind_speed_10m_max", 0.0)
        out = []
        for i, d in enumerate(dates[:days]):
            if i >= min(len(rain), len(prob), len(tmax), len(tmin), len(wind)):
                break
            out.append(DayOutlook(
                date=d, rain_mm=round(float(rain[i]), 1), rain_prob_pct=round(float(prob[i]), 0),
                max_temp_c=round(float(tmax[i]), 1), min_temp_c=round(float(tmin[i]), 1),
                wind_kmh=round(float(wind[i]), 1),
            ))
        return out

    def _build_mock_snapshot(self, lat: float, lon: float) -> EnvironmentalSnapshot:
        return EnvironmentalSnapshot(
            latitude=round(lat, 4),
            longitude=round(lon, 4),
            forecast_max_temp_c=31.5,
            forecast_min_temp_c=18.5,
            forecast_rain_24h_mm=0.0,
            forecast_rain_48h_mm=0.0,
            forecast_rain_7d_mm=2.0,
            rain_probability_pct=15.0,
            wind_speed_kmh=9.5,
            relative_humidity_pct=45.0,
            soil_moisture_0_7cm_pct=29.0,
            soil_moisture_7_28cm_pct=33.5,
            soil_temp_0_7cm_c=24.5,
            soil_texture_class="Clay Loam (Black Cotton Soil)",
            consecutive_dry_days=10,
            cumulative_rain_30d_mm=12.0,
            data_confidence="HIGH",
            sources_used=["Open-Meteo (Simulated)", "NASA POWER (Simulated)", "ISRIC SoilGrids (Simulated)"]
        )
