import asyncio
import logging
from typing import Dict, Any, Tuple
import httpx

from app.config import settings
from app.services.data_clients.base import BaseDataClient

logger = logging.getLogger(__name__)

class ISRICSoilGridsClient(BaseDataClient):
    """
    Client for ISRIC SoilGrids 2.0 REST API (250m resolution).
    Fetches clay, sand, and silt fractions (0-5cm and 5-15cm depths)
    and resolves USDA / Indian Soil Taxonomy classification.
    Permanently cached per location since soil texture does not change.
    """
    def __init__(self):
        super().__init__(
            ttl_seconds=settings.CACHE_SOIL_TTL_SEC, # Permanent (1 yr+)
            timeout_seconds=7.0,
            max_retries=2
        )
        self.base_url = "https://rest.isric.org/soilgrids/v2.0/properties/query"

    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        cache_key = self._get_location_key(lat, lon, "soilgrids")
        cached = self.get_cached(cache_key)
        if cached is not None:
            logger.info(f"SoilGrids permanent cache hit for ({lat}, {lon})")
            return cached, True

        params = [
            ("lat", round(lat, 4)),
            ("lon", round(lon, 4)),
            ("property", "clay"),
            ("property", "sand"),
            ("property", "silt"),
            ("depth", "0-5cm"),
            ("depth", "5-15cm"),
            ("value", "mean")
        ]

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
                        logger.warning(f"SoilGrids returned status {resp.status_code}")
            except Exception as e:
                logger.warning(f"SoilGrids attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        logger.info(f"SoilGrids unavailable for ({lat}, {lon}). Falling back to Maharashtra Vertisol / Clay Loam baseline.")
        fallback = self._get_fallback()
        self.set_cached(cache_key, fallback)
        return fallback, False

    def _parse_response(self, raw: dict) -> Dict[str, Any]:
        layers = raw.get("properties", {}).get("layers", [])
        clay_pct = 42.0
        sand_pct = 25.0
        silt_pct = 33.0

        for layer in layers:
            name = layer.get("name")
            depths = layer.get("depths", [])
            if depths:
                mean_val = depths[0].get("values", {}).get("mean")
                if mean_val is not None:
                    # SoilGrids returns fractions in g/kg (permille). Divide by 10 for %.
                    val_pct = mean_val / 10.0
                    if name == "clay":
                        clay_pct = val_pct
                    elif name == "sand":
                        sand_pct = val_pct
                    elif name == "silt":
                        silt_pct = val_pct

        soil_class = self._determine_soil_class(clay_pct, sand_pct, silt_pct)

        return {
            "source": "ISRIC SoilGrids (250m)",
            "clay_pct": round(clay_pct, 1),
            "sand_pct": round(sand_pct, 1),
            "silt_pct": round(silt_pct, 1),
            "soil_texture_class": soil_class
        }

    def _determine_soil_class(self, clay: float, sand: float, silt: float) -> str:
        """Derive standard USDA / Indian soil texture classification."""
        if clay >= 45.0:
            return "Heavy Black Clay (Vertisol)"
        elif clay >= 35.0:
            return "Clay Loam (Black Cotton Soil)"
        elif sand >= 60.0:
            return "Sandy Loam"
        elif silt >= 50.0:
            return "Silt Loam"
        else:
            return "Medium Clay Loam"

    def _get_fallback(self) -> Dict[str, Any]:
        return {
            "source": "ISRIC Regional Baseline (Maharashtra Vertisol)",
            "clay_pct": 44.0,
            "sand_pct": 24.0,
            "silt_pct": 32.0,
            "soil_texture_class": "Clay Loam (Black Cotton Soil)"
        }
