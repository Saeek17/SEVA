"use client";

import { useEffect, useRef, useState } from "react";
import { Farmer } from "@/lib/types";
import { Search, MapPin, Locate } from "lucide-react";

interface FarmerMapProps {
  farmers: Farmer[];
  selectedFarmerId?: string;
  onSelectFarmer?: (farmer: Farmer) => void;
  onSelectCoordinates?: (lat: number, lon: number, district?: string) => void;
  interactive?: boolean;
  center?: [number, number];
}

export function FarmerMap({
  farmers,
  selectedFarmerId,
  onSelectFarmer,
  onSelectCoordinates,
  interactive = true,
  center = [19.2, 75.5],
}: FarmerMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const activePinRef = useRef<any>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const popularLocations: Record<string, [number, number]> = {
    "pune": [18.5204, 73.8567],
    "nashik": [19.9975, 73.7898],
    "latur": [18.4088, 76.5604],
    "ahmednagar": [19.0948, 74.7480],
    "akola": [20.7002, 77.0082],
    "baramati": [18.1517, 74.5775],
    "kolhapur": [16.7050, 74.2433],
    "solapur": [17.6599, 75.9064],
    "nagpur": [21.1458, 79.0882],
    "amravati": [20.9374, 77.7796],
    "nanded": [19.1383, 77.3210],
    "sangli": [16.8524, 74.5815],
    "satara": [17.6805, 73.9997],
    "dindori": [20.2052, 73.8329],
  };

  const cropColors: Record<string, { color: string; letter: string }> = {
    rice: { color: "#2563eb", letter: "R" },
    wheat: { color: "#d97706", letter: "W" },
    cotton: { color: "#0284c7", letter: "C" },
    maize: { color: "#ca8a04", letter: "M" },
    tomato: { color: "#dc2626", letter: "T" },
    sugarcane: { color: "#059669", letter: "S" },
    soybean: { color: "#16a34a", letter: "S" },
  };

  const getCropStyle = (cropId: string) => {
    const id = (cropId || "").toLowerCase();
    for (const key of Object.keys(cropColors)) {
      if (id.includes(key)) return cropColors[key];
    }
    return { color: "#059669", letter: "🌱" };
  };

  const jumpToLocation = (lat: number, lon: number, name?: string) => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([lat, lon], 10);
      if (onSelectCoordinates) {
        onSelectCoordinates(Number(lat.toFixed(4)), Number(lon.toFixed(4)), name);
      }
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = searchQuery.trim().toLowerCase();
    for (const [city, coords] of Object.entries(popularLocations)) {
      if (city.includes(clean) || clean.includes(city)) {
        jumpToLocation(coords[0], coords[1], city.toUpperCase());
        return;
      }
    }
  };

  useEffect(() => {
    if (typeof window === "undefined" || !mapContainerRef.current) return;

    let isMounted = true;

    import("leaflet").then((L) => {
      if (!isMounted || !mapContainerRef.current) return;

      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (!mapInstanceRef.current) {
        const map = L.map(mapContainerRef.current).setView(center, 7);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 18,
        }).addTo(map);

        if (onSelectCoordinates && interactive) {
          map.on("click", (e: any) => {
            const lat = Number(e.latlng.lat.toFixed(4));
            const lon = Number(e.latlng.lng.toFixed(4));
            onSelectCoordinates(lat, lon);

            // Move active temp pin
            if (activePinRef.current) {
              map.removeLayer(activePinRef.current);
            }
            const activeIcon = L.divIcon({
              className: "active-pin",
              html: `<div style="background-color: #047857; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; color: white; font-size: 13px; font-weight: bold;">
                📍
              </div>`,
              iconSize: [30, 30],
              iconAnchor: [15, 15],
            });
            activePinRef.current = L.marker([lat, lon], { icon: activeIcon }).addTo(map);
          });
        }

        mapInstanceRef.current = map;
      }

      const map = mapInstanceRef.current;

      // Clear previous farmer markers
      markersRef.current.forEach((m) => map.removeLayer(m));
      markersRef.current = [];

      // Add pins for farmers
      farmers.forEach((farmer) => {
        const style = getCropStyle(farmer.crop_id);
        const isSelected = farmer.id === selectedFarmerId;

        const customIcon = L.divIcon({
          className: "custom-farmer-pin",
          html: `<div style="background-color: ${style.color}; width: ${isSelected ? "32px" : "26px"}; height: ${
            isSelected ? "32px" : "26px"
          }; border-radius: 50%; border: 3px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-size: ${
            isSelected ? "13px" : "11px"
          }; font-weight: bold; transform: ${isSelected ? "scale(1.15)" : "none"};">
            ${style.letter}
          </div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14],
          popupAnchor: [0, -14],
        });

        const marker = L.marker([farmer.latitude, farmer.longitude], { icon: customIcon }).addTo(map);

        const popupContent = `
          <div style="font-family: inherit; min-width: 170px;">
            <h4 style="font-weight: 700; margin: 0 0 4px; font-size: 14px; color: #0f172a;">${farmer.full_name}</h4>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">${farmer.phone_masked} • ${farmer.district || "Maharashtra"}</div>
            <div style="display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; background: ${style.color}20; color: ${style.color};">
              ${farmer.crop_id.replace("_maharashtra", "").toUpperCase()}
            </div>
            <div style="font-size: 11px; color: #475569; margin-top: 6px;">Sown: ${farmer.sowing_date} (${farmer.language.toUpperCase()})</div>
          </div>
        `;

        marker.bindPopup(popupContent);
        marker.on("click", () => {
          if (onSelectFarmer) onSelectFarmer(farmer);
        });

        markersRef.current.push(marker);
      });
    });

    return () => {
      isMounted = false;
    };
  }, [farmers, selectedFarmerId]);

  return (
    <div className="relative w-full h-full min-h-[380px] rounded-3xl overflow-hidden shadow-xs border border-slate-200">
      {/* Map Search & Quick Jump Overlay */}
      {interactive && (
        <div className="absolute top-3 left-3 z-[1000] flex items-center gap-1.5 bg-white/95 backdrop-blur-md p-1.5 rounded-2xl shadow-lg border border-slate-200 text-xs">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            <input
              type="text"
              placeholder="Search Pune, Nashik, Latur..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-2 py-1 bg-transparent text-xs text-slate-800 focus:outline-none w-36 sm:w-44 font-medium"
            />
            <button
              type="submit"
              className="px-2.5 py-1 rounded-xl bg-emerald-600 text-white font-bold hover:bg-emerald-700 transition"
            >
              Go
            </button>
          </form>

          <button
            type="button"
            onClick={() => jumpToLocation(18.5204, 73.8567, "Pune")}
            className="p-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600"
            title="Reset to Maharashtra Center"
          >
            <Locate className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full min-h-[380px]" />
    </div>
  );
}
