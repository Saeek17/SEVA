import pytest
import asyncio
from app.services.data_clients.base import BaseDataClient
from app.services.data_clients.aggregator import EnvironmentalAggregator

class DummyClient(BaseDataClient):
    def __init__(self, ttl: int = 1):
        super().__init__(ttl_seconds=ttl)
        self.call_count = 0

    async def fetch(self, lat: float, lon: float):
        key = self._get_location_key(lat, lon, "dummy")
        cached = self.get_cached(key)
        if cached:
            return cached, True
        self.call_count += 1
        data = {"temp": 25.0, "call_count": self.call_count}
        self.set_cached(key, data)
        return data, True

@pytest.mark.asyncio
async def test_base_client_caching_and_ttl():
    client = DummyClient(ttl=1)
    # First call: hits API
    res1, ok1 = await client.fetch(18.5204, 73.8567)
    assert ok1 is True
    assert res1["call_count"] == 1

    # Second call within TTL: should hit cache
    res2, ok2 = await client.fetch(18.5201, 73.8569) # Close coordinates rounding to same 3 decimals
    assert ok2 is True
    assert res2["call_count"] == 1

    # Wait for TTL expiry
    await asyncio.sleep(1.1)
    res3, ok3 = await client.fetch(18.5204, 73.8567)
    assert ok3 is True
    assert res3["call_count"] == 2

@pytest.mark.asyncio
async def test_aggregator_mock_snapshot():
    aggregator = EnvironmentalAggregator()
    snapshot = await aggregator.get_environmental_snapshot(18.52, 73.85, force_mock=True)
    assert snapshot.latitude == 18.52
    assert snapshot.soil_texture_class is not None
    assert snapshot.data_confidence == "HIGH"
    assert len(snapshot.sources_used) >= 1
