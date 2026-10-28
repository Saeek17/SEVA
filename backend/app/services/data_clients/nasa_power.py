import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import httpx

from app.config import settings
from app.services.data_clients.base import BaseDataClient

logger = logging.getLogger(__name__)

class NasaPowerClient(BaseDataClient):
    """
    Client for NASA POWER Daily Agrometeorology API.
    Fetches past 30 days of precipitation and temperature data to compute:
    1. Consecutive dry days (daily rain < 2.5 mm).
    2. 30-day cumulative precipitation.
    """
    def __init__(self):
        super().__init__(
            ttl_seconds=settings.CACHE_HISTORICAL_TTL_SEC,
            timeout_seconds=7.0,
            max_retries=2
        )
        self.base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        cache_key = self._get_location_key(lat, lon, "nasa_power")
        cached = self.get_cached(cache_key)
        if cached is not None:
            logger.info(f"NASA POWER cache hit for ({lat}, {lon})")
            return cached, True

        # Calculate 30-day window ending 2 days ago (NASA POWER has a 2-day reporting latency)
        end_date = datetime.utcnow() - timedelta(days=2)
        start_date = end_date - timedelta(days=30)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        params = {
            "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
            "community": "AG",
            "longitude": round(lon, 4),
            "latitude": round(lat, 4),
            "start": start_str,
            "end": end_str,
            "format": "JSON"
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
                        logger.warning(f"NASA POWER returned status {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"NASA POWER attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        logger.error(f"NASA POWER all attempts failed for ({lat}, {lon}). Falling back to degraded estimates.")
        fallback = self._get_fallback()
        return fallback, False

    def _parse_response(self, raw: dict) -> Dict[str, Any]:
        properties = raw.get("properties", {})
        parameter = properties.get("parameter", {})
        precip_dict = parameter.get("PRECTOTCORR", {})

        # Sorted list of daily precipitation values
        sorted_dates = sorted(precip_dict.keys())
        daily_rains = [precip_dict[d] for d in sorted_dates if precip_dict[d] is not None and precip_dict[d] >= 0]

        cumulative_30d = sum(daily_rains) if daily_rains else 0.0

        # Calculate consecutive dry days ending at the most recent recorded date
        # Agromet standard: dry day is rain < 2.5 mm
        dry_days = 0
        for rain in reversed(daily_rains):
            if rain < 2.5:
                dry_days += 1
            else:
                break

        return {
            "source": "NASA POWER API (30-day reanalysis)",
            "consecutive_dry_days": dry_days,
            "cumulative_rain_30d_mm": round(cumulative_30d, 1),
            "historical_daily_count": len(daily_rains)
        }

    def _get_fallback(self) -> Dict[str, Any]:
        return {
            "source": "NASA POWER Degraded (Default Climatology)",
            "consecutive_dry_days": 3,
            "cumulative_rain_30d_mm": 45.0,
            "historical_daily_count": 0
        }
