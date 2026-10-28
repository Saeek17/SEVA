"use client";

import { useState, useEffect } from "react";
import {
  Compass,
  Play,
  CloudSun,
  Sprout,
  Cpu,
  Sparkles,
  ShieldCheck,
  AlertCircle,
  Volume2,
  Droplets,
  Wind,
  Thermometer,
  Layers,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock
} from "lucide-react";
import { api } from "@/lib/api";
import { CropMetadata, SimulationResult } from "@/lib/types";
import { AudioPlayer } from "@/components/AudioPlayer";

export default function SimulatePage() {
  const [crops, setCrops] = useState<CropMetadata[]>([]);
  const [selectedCropId, setSelectedCropId] = useState("wheat_maharashtra");
  const [latitude, setLatitude] = useState(18.5204);
  const [longitude, setLongitude] = useState(73.8567);
  const [das, setDas] = useState(21);
  const [language, setLanguage] = useState("hi");
  const [farmerName, setFarmerName] = useState("Baburao Patil");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getCrops().then((data) => {
      setCrops(data);
      if (data.length > 0) setSelectedCropId(data[0].crop_id);
    }).catch(console.error);
  }, []);

  const presets = [
    {
      name: "Wheat CRI Irrigation Need (Pune)",
      cropId: "wheat_maharashtra",
      lat: 18.5204,
      lon: 73.8567,
      das: 21,
      lang: "hi",
      farmer: "Ramesh Pawar",
    },
    {
      name: "Soybean Impending Rain Skip (Latur)",
      cropId: "soybean_maharashtra",
      lat: 18.4088,
      lon: 76.5604,
      das: 48,
      lang: "mr",
      farmer: "Suresh Deshmukh",
    },
    {
      name: "Soybean High Wind Spray Hazard (Akola)",
      cropId: "soybean_maharashtra",
      lat: 20.7002,
      lon: 77.0082,
      das: 45,
      lang: "mr",
      farmer: "Ganesh Kulkarni",
    },
    {
      name: "Wheat Terminal Heat Alert (Ahmednagar)",
      cropId: "wheat_maharashtra",
      lat: 19.0948,
      lon: 74.7480,
      das: 75,
      lang: "en",
      farmer: "Kishore Jadhav",
    },
  ];

  const applyPreset = (p: typeof presets[0]) => {
    setSelectedCropId(p.cropId);
    setLatitude(p.lat);
    setLongitude(p.lon);
    setDas(p.das);
    setLanguage(p.lang);
    setFarmerName(p.farmer);
  };

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.simulateFarmer({
        latitude: Number(latitude),
        longitude: Number(longitude),
        crop_id: selectedCropId,
        das: Number(das),
        language,
        farmer_name: farmerName,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case "IRRIGATE":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "SKIP_IRRIGATION":
        return "bg-slate-100 text-slate-800 border-slate-300";
      case "SAFE_SPRAY":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "AVOID_SPRAY":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "HEAT_ALERT":
      case "RAIN_ALERT":
      case "DROUGHT_ALERT":
        return "bg-rose-100 text-rose-800 border-rose-300";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Title */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              Hyperlocal Pipeline Sandbox Simulator
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Trace the end-to-end advisory engine live: Raw Data &rarr; Rules Engine &rarr; Structured Advice &rarr; LLM Message &rarr; Audio Preview.
            </p>
          </div>
        </div>
      </div>

      {/* Preset Scenarios */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Quick-Load Scenario Presets
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {presets.map((p) => (
            <button
              key={p.name}
              onClick={() => applyPreset(p)}
              className="text-left p-3 rounded-2xl border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50/40 transition group"
            >
              <p className="text-xs font-bold text-slate-900 group-hover:text-emerald-700">{p.name}</p>
              <p className="text-[11px] text-slate-500 mt-1">
                {p.cropId.replace("_maharashtra", "")} • DAS {p.das} • {p.lang.toUpperCase()}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Input Controls Form */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-5">
        <h3 className="text-base font-bold text-slate-900">Simulation Parameters</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Crop (Dynamic Config)</label>
            <select
              value={selectedCropId}
              onChange={(e) => setSelectedCropId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {crops.map((c) => (
                <option key={c.crop_id} value={c.crop_id}>
                  {c.common_name_en} ({c.common_name_hi})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Days After Sowing (DAS)</label>
            <input
              type="number"
              min="1"
              max="150"
              value={das}
              onChange={(e) => setDas(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Latitude</label>
            <input
              type="number"
              step="0.0001"
              value={latitude}
              onChange={(e) => setLatitude(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Longitude</label>
            <input
              type="number"
              step="0.0001"
              value={longitude}
              onChange={(e) => setLongitude(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Vernacular Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="hi">Hindi (सरल हिंदी)</option>
              <option value="mr">Marathi (मराठी)</option>
              <option value="en">English (Plain)</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-md shadow-emerald-600/20 disabled:opacity-60"
          >
            <Play className={`w-4 h-4 fill-current ${loading ? "animate-spin" : ""}`} />
            {loading ? "Running Pipeline..." : "Execute Simulation"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simulation Visual Trace */}
      {result && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <h2 className="text-xl font-black text-slate-900">Pipeline Execution Inspection</h2>
            <span className="text-xs font-semibold px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
              Confidence: {result.environmental_data.data_confidence}
            </span>
          </div>

          {/* STEP 1: Environmental Facts */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Hyperlocal Environmental Facts</h3>
                  <p className="text-xs text-slate-500">Live API aggregated & cached</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 text-[11px] font-semibold text-slate-600">
                {result.environmental_data.sources_used.map((s) => (
                  <span key={s} className="px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <Thermometer className="w-3.5 h-3.5 text-rose-500" /> Max / Min Temp
                </span>
                <p className="text-base font-black text-slate-900 mt-1">
                  {result.environmental_data.forecast_max_temp_c}°C / {result.environmental_data.forecast_min_temp_c}°C
                </p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <Droplets className="w-3.5 h-3.5 text-blue-500" /> Forecast Rain (48h)
                </span>
                <p className="text-base font-black text-slate-900 mt-1">
                  {result.environmental_data.forecast_rain_48h_mm} mm
                </p>
                <span className="text-[10px] text-slate-400">Prob: {result.environmental_data.rain_probability_pct}%</span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <Wind className="w-3.5 h-3.5 text-teal-500" /> Wind Speed
                </span>
                <p className="text-base font-black text-slate-900 mt-1">
                  {result.environmental_data.wind_speed_kmh} km/h
                </p>
                <span className="text-[10px] text-slate-400">RH: {result.environmental_data.relative_humidity_pct}%</span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-amber-500" /> Soil Moisture (0-7cm)
                </span>
                <p className="text-base font-black text-slate-900 mt-1">
                  {result.environmental_data.soil_moisture_0_7cm_pct}%
                </p>
                <span className="text-[10px] text-slate-400">7-28cm: {result.environmental_data.soil_moisture_7_28cm_pct}%</span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-purple-500" /> Dry Spell Length
                </span>
                <p className="text-base font-black text-slate-900 mt-1">
                  {result.environmental_data.consecutive_dry_days} days
                </p>
                <span className="text-[10px] text-slate-400">30d Rain: {result.environmental_data.cumulative_rain_30d_mm}mm</span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <Sprout className="w-3.5 h-3.5 text-emerald-500" /> Soil Classification
                </span>
                <p className="text-xs font-bold text-slate-900 mt-1 line-clamp-2">
                  {result.environmental_data.soil_texture_class}
                </p>
                <span className="text-[10px] text-slate-400">ISRIC 250m</span>
              </div>
            </div>
          </div>

          {/* STEP 2 & 3: Crop Stage & Deterministic Rules Engine */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Step 2: Growth Stage (4 cols) */}
            <div className="lg:col-span-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Growth Stage Resolution</h3>
                  <p className="text-xs text-slate-500">Days After Sowing (DAS): {result.das}</p>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-200/60 space-y-2">
                <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">Active Stage</span>
                <h4 className="text-base font-black text-slate-900">{result.growth_stage}</h4>
                <p className="text-xs text-slate-600 font-medium">
                  Crop: <strong>{result.crop_name}</strong> ({result.crop_id})
                </p>
              </div>
            </div>

            {/* Step 3: Rules Engine Output (8 cols) */}
            <div className="lg:col-span-8 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-sm">
                    3
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Deterministic Rules Engine Output</h3>
                    <p className="text-xs text-slate-500">Decisions derived from SAU Package of Practices</p>
                  </div>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                  {result.advice_items.length} Evaluated Actions
                </span>
              </div>

              <div className="space-y-3">
                {result.advice_items.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-slate-100/60 transition space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-black px-2.5 py-1 rounded-full border ${getActionBadgeColor(item.action)}`}>
                          {item.action.replace("_", " ")}
                        </span>
                        <span className="text-xs font-mono font-semibold text-slate-700">
                          {item.reason_code}
                        </span>
                      </div>
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                        item.urgency === "HIGH"
                          ? "bg-rose-100 text-rose-700"
                          : item.urgency === "MEDIUM"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-slate-200 text-slate-700"
                      }`}>
                        Urgency: {item.urgency}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600">
                      <strong>Parameters:</strong> {JSON.stringify(item.params)}
                    </div>

                    {item.sources_used && item.sources_used.length > 0 && (
                      <div className="text-[11px] text-slate-500">
                        <strong>Citation:</strong> {item.sources_used[item.sources_used.length - 1]}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* STEP 4 & 5: LLM Scribe, Guardrail Validation & Audio Preview */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Step 4: Vernacular Message & Guardrail (7 cols) */}
            <div className="lg:col-span-7 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm">
                    4
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Vernacular LLM Formatting & Guardrail</h3>
                    <p className="text-xs text-slate-500">Translates structured advice into SMS &lt;320 chars</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {result.validation_passed ? (
                    <span className="flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Guardrail Passed
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                      <XCircle className="w-3.5 h-3.5" /> DLT Fallback Activated
                    </span>
                  )}
                </div>
              </div>

              {/* Message Box */}
              <div className="p-5 rounded-2xl bg-slate-900 text-white shadow-lg space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>SMS Payload Delivery Content</span>
                  <span className="font-mono text-emerald-400">
                    {result.generated_message.length} / 320 characters
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-100 leading-relaxed font-sans">
                  &quot;{result.generated_message}&quot;
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                  <span>Fallback Mode: {result.fallback_used}</span>
                  <span>Validation: {result.validation_notes || "All checks passed"}</span>
                </div>
              </div>
            </div>

            {/* Step 5: Voice Call Audio Preview (5 cols) */}
            <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold text-sm">
                    5
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Automated Voice Call Audio</h3>
                    <p className="text-xs text-slate-500">Google Cloud TTS stream</p>
                  </div>
                </div>
                <p className="text-xs text-slate-600 mb-4">
                  Farmers who cannot read SMS receive an automated outbound phone call with identical agronomic guidance.
                </p>
              </div>

              <AudioPlayer
                audioUrl={result.voice_audio_url}
                language={result.language}
                label={`Audio for ${farmerName}`}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
