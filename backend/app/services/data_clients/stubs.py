from typing import Dict, Any, Tuple
from app.services.data_clients.base import BaseDataClient

class IMDGriddedClient(BaseDataClient):
    """
    [Phase 2 Design] IMD Gridded Rainfall Client.
    Fetches daily 0.25° x 0.25° gridded rainfall data from IMD Pune (imdpune.gov.in).
    Binary/NetCDF gridded files updated daily at 08:30 IST.
    """
    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        raise NotImplementedError("IMD Gridded Client is scheduled for Phase 2 integration.")

class CHIRPSPrecipitationClient(BaseDataClient):
    """
    [Phase 2 Design] Climate Hazards Group InfraRed Precipitation with Station data (CHIRPS).
    Provides quasi-global 0.05° resolution daily precipitation for drought monitoring.
    """
    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        raise NotImplementedError("CHIRPS Precipitation Client is scheduled for Phase 2 integration.")

class NASAGPMClient(BaseDataClient):
    """
    [Phase 2 Design] NASA Global Precipitation Measurement (GPM-IMERG).
    Early-run precipitation estimates at 0.1° resolution every 30 minutes.
    """
    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        raise NotImplementedError("NASA GPM Client is scheduled for Phase 2 integration.")

class NASASMAPSoilClient(BaseDataClient):
    """
    [Phase 2 Design] NASA Soil Moisture Active Passive (SMAP) L3/L4.
    Enhanced 9km / 3km surface and root-zone soil moisture estimates.
    """
    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        raise NotImplementedError("NASA SMAP Client is scheduled for Phase 2 integration.")

class Sentinel2NDVIClient(BaseDataClient):
    """
    [Phase 2 Design] Sentinel-2 10m Normalized Difference Vegetation Index (NDVI).
    Accesses Copernicus Data Space STAC API / Google Earth Engine to compute
    canopy vigor and crop stress index every 5 days.
    """
    async def fetch(self, lat: float, lon: float) -> Tuple[Dict[str, Any], bool]:
        raise NotImplementedError("Sentinel-2 NDVI Client is scheduled for Phase 2 integration.")
