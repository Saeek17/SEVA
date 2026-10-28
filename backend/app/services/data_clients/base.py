import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class CacheEntry:
    def __init__(self, data: Any, expires_at: float):
        self.data = data
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class BaseDataClient(ABC):
    """
    Abstract Base Client for all environmental data providers.
    Provides in-memory caching with TTL, location coordinate rounding,
    retry logic with backoff, and graceful fallback.
    """
    _cache: Dict[str, CacheEntry] = {}

    def __init__(self, ttl_seconds: int = 10800, timeout_seconds: float = 8.0, max_retries: int = 2):
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @classmethod
    def _get_location_key(cls, lat: float, lon: float, prefix: str) -> str:
        # 3 decimal places gives ~110 meters spatial grouping
        return f"{prefix}:{round(lat, 3)}:{round(lon, 3)}"

    def get_cached(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry:
            if not entry.is_expired():
                return entry.data
            else:
                del self._cache[key]
        return None

    def set_cached(self, key: str, data: Any, custom_ttl: Optional[int] = None):
        ttl = custom_ttl if custom_ttl is not None else self.ttl_seconds
        self._cache[key] = CacheEntry(data, time.time() + ttl)

    @abstractmethod
    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        """
        Fetch data for the given coordinates.
        Returns: Tuple of (data_dict, is_success)
        """
        pass
