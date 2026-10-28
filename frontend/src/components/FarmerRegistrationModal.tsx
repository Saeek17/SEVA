"use client";

import { useState, useEffect } from "react";
import { X, CheckCircle2, AlertCircle, MapPin, Sprout, Search } from "lucide-react";
import { CropMetadata } from "@/lib/types";
import { api } from "@/lib/api";

interface FarmerRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newFarmer?: any) => void;
  crops: CropMetadata[];
}

export function FarmerRegistrationModal({
  isOpen,
  onClose,
  onSuccess,
  crops,
}: FarmerRegistrationModalProps) {
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [language, setLanguage] = useState("mr");
  const [selectedCropId, setSelectedCropId] = useState("tomato_maharashtra");
  const [farmingStage, setFarmingStage] = useState("Flowering");
  const [landAcreage, setLandAcreage] = useState("3.5");
  const [sowingDate, setSowingDate] = useState("2024-10-01");
  const [district, setDistrict] = useState("Nashik");
  const [locationQuery, setLocationQuery] = useState("Nashik, Maharashtra");
  const [latitude, setLatitude] = useState(19.9975);
  const [longitude, setLongitude] = useState(73.7898);
  const [consentSms, setConsentSms] = useState(true);
  const [consentVoice, setConsentVoice] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSowingDate(new Date().toISOString().split("T")[0]);
  }, []);

  if (!isOpen) return null;

  // Preset locations for quick selection
  const locationPresets = [
    { name: "Nashik (Dindori/Niphad)", lat: 20.0063, lon: 73.8077, district: "Nashik" },
    { name: "Pune (Baramati/Khed)", lat: 18.5204, lon: 73.8567, district: "Pune" },
    { name: "Latur (Ausa/Udgir)", lat: 18.4088, lon: 76.5604, district: "Latur" },
    { name: "Ahmednagar (Rahuri)", lat: 19.3889, lon: 74.6481, district: "Ahmednagar" },
    { name: "Akola (Murtizapur)", lat: 20.7002, lon: 77.0082, district: "Akola" },
    { name: "Kolhapur (Karveer/Shirol)", lat: 16.7050, lon: 74.2433, district: "Kolhapur" },
    { name: "Nagpur (Katol/Ramtek)", lat: 21.1458, lon: 79.0882, district: "Nagpur" },
  ];

  // All crops matching user's Image 2
  const allCropsList = [
    {
      id: "rice_maharashtra",
      name: "Rice (Paddy)",
      sub: "Cereal Grain",
      tag: "High Water",
      emoji: "🌾",
    },
    {
      id: "wheat_maharashtra",
      name: "Wheat",
      sub: "Rabi Cereal",
      tag: "Moderate",
      emoji: "🌱",
    },
    {
      id: "cotton_maharashtra",
      name: "Cotton",
      sub: "Fiber Commercial",
      tag: "Moderate",
      emoji: "☁️",
    },
    {
      id: "maize_maharashtra",
      name: "Maize (Corn)",
      sub: "Kharif Coarse Grain",
      tag: "Moderate",
      emoji: "🌽",
    },
    {
      id: "tomato_maharashtra",
      name: "Tomato",
      sub: "Vegetable / Solanaceous",
      tag: "Sensitive",
      emoji: "🍅",
    },
    {
      id: "sugarcane_maharashtra",
      name: "Sugarcane",
      sub: "Cash Crop / Perennial",
      tag: "Very High",
      emoji: "🎋",
    },
    {
      id: "soybean_maharashtra",
      name: "Soybean",
      sub: "Kharif Oilseed",
      tag: "Moderate",
      emoji: "🌿",
    },
  ];

  // Stages matching user's Image 3
  const farmingStages = [
    { phase: "Phase 1", name: "Preparing land", das: 1 },
    { phase: "Phase 2", name: "Planting", das: 10 },
    { phase: "Phase 3", name: "Growing", das: 30 },
    { phase: "Phase 4", name: "Flowering", das: 55 },
    { phase: "Phase 5", name: "Harvesting", das: 95 },
  ];

  const handleLocationPreset = (p: typeof locationPresets[0]) => {
    setLocationQuery(p.name);
    setDistrict(p.district);
    setLatitude(p.lat);
    setLongitude(p.lon);
  };

  const handleManualLocationChange = (text: string) => {
    setLocationQuery(text);
    // Simple matching against known districts
    const match = locationPresets.find((p) =>
      p.name.toLowerCase().includes(text.toLowerCase()) ||
      p.district.toLowerCase().includes(text.toLowerCase())
    );
    if (match) {
      setDistrict(match.district);
      setLatitude(match.lat);
      setLongitude(match.lon);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanPhone = phoneNumber.replace(/[\s\-\(\)]/g, "");
    if (!/^(?:\+91|91|0)?[6-9]\d{9}$/.test(cleanPhone)) {
      setError("Please enter a valid 10-digit Indian mobile number (+91XXXXXXXXXX).");
      return;
    }

    if (!consentSms || !consentVoice) {
      setError("Farmer consent for SMS/Voice is required by telecom regulations.");
      return;
    }

    setLoading(true);
    try {
      const selectedStageObj = farmingStages.find((s) => s.name === farmingStage);
      const computedDas = selectedStageObj ? selectedStageObj.das : 50;

      const registered = await api.registerFarmer({
        full_name: fullName,
        phone_number: cleanPhone,
        language,
        latitude: Number(latitude),
        longitude: Number(longitude),
        district,
        crop_id: selectedCropId,
        sowing_date: sowingDate,
        consent_sms: consentSms,
        consent_voice: consentVoice,
      });

      // Pass context for pipeline stepper
      const newFarmerContext = {
        farmerName: fullName,
        phone: cleanPhone,
        district,
        lat: Number(latitude),
        lon: Number(longitude),
        cropId: selectedCropId,
        cropName: allCropsList.find((c) => c.id === selectedCropId)?.name || "Crop",
        stage: farmingStage,
        das: computedDas,
        acreage: `${landAcreage} Acres`,
        language,
      };

      onSuccess(newFarmerContext);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to register farmer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl border border-slate-100 max-h-[92vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-150 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-inner">
              <Sprout className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-black text-slate-900">Onboard New Farmer</h3>
              <p className="text-xs text-slate-500">
                Hyperlocal Climate Intelligence • Smallholder Registration
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 flex items-center gap-2.5 text-xs text-rose-800">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 1. Basic Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Farmer Full Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Ramesh Patil / शांताराम पवार"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Mobile Number (SMS & Voice) *
              </label>
              <input
                type="tel"
                required
                placeholder="+91 98765 43210"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* 2. Manual Location Search & Coordinate Sync */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                <span>Field Location & Coordinates Sync</span>
              </label>
              <span className="text-[11px] font-semibold text-emerald-700">Auto-Synched</span>
            </div>

            <div>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Type city, taluka, or district (e.g. Pune, Nashik, Baramati...)"
                  value={locationQuery}
                  onChange={(e) => handleManualLocationChange(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              {/* Quick Preset Buttons */}
              <div className="flex flex-wrap gap-1.5 mt-2">
                {locationPresets.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    onClick={() => handleLocationPreset(p)}
                    className={`text-[11px] px-2.5 py-1 rounded-lg border transition font-medium ${
                      district.toLowerCase() === p.district.toLowerCase()
                        ? "bg-emerald-600 text-white border-emerald-600"
                        : "bg-white text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Manual Lat/Long editable inputs */}
            <div className="grid grid-cols-3 gap-2.5 pt-1">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">District</label>
                <input
                  type="text"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs bg-white font-medium"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Latitude (°N)</label>
                <input
                  type="number"
                  step="0.0001"
                  value={latitude}
                  onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs bg-white font-mono"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Longitude (°E)</label>
                <input
                  type="number"
                  step="0.0001"
                  value={longitude}
                  onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs bg-white font-mono"
                />
              </div>
            </div>
          </div>

          {/* 3. SELECT CROP (Matching user's Image 2) */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              SELECT CROP
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {allCropsList.map((crop) => {
                const isSelected = selectedCropId === crop.id;
                return (
                  <button
                    key={crop.id}
                    type="button"
                    onClick={() => setSelectedCropId(crop.id)}
                    className={`p-3 rounded-2xl border text-left transition flex flex-col justify-between relative cursor-pointer ${
                      isSelected
                        ? "bg-emerald-50/60 border-emerald-600 ring-2 ring-emerald-500/20"
                        : "bg-white border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {isSelected && (
                      <span className="absolute top-2.5 right-2.5 w-4 h-4 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px]">
                        ✓
                      </span>
                    )}
                    <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-lg mb-1.5">
                      {crop.emoji}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 leading-tight">{crop.name}</h4>
                      <p className="text-[10px] text-slate-500 leading-tight">{crop.sub}</p>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400 mt-2">
                      {crop.tag}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 4. CURRENT FARMING STAGE (Matching user's Image 3) & LAND CHOOSING */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                CURRENT FARMING STAGE
              </label>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                Selected: {farmingStage}
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Crucial for determining whether the crop is vulnerable to blossom drop, germination rot, or moisture deficit.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {farmingStages.map((stg) => {
                const isSelected = farmingStage === stg.name;
                return (
                  <button
                    key={stg.name}
                    type="button"
                    onClick={() => setFarmingStage(stg.name)}
                    className={`py-2.5 px-2 rounded-2xl border text-center transition cursor-pointer ${
                      isSelected
                        ? "bg-[#144d37] text-white border-[#144d37] shadow-sm font-bold"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    <p className="text-xs leading-tight font-bold">{stg.name}</p>
                    <p className={`text-[10px] mt-0.5 ${isSelected ? "text-emerald-200" : "text-slate-400"}`}>
                      {stg.phase}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Land Acreage Selection */}
            <div className="pt-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Land Size / Acreage
              </label>
              <div className="grid grid-cols-4 gap-2">
                {["1.0", "2.5", "3.5", "5.0"].map((ac) => (
                  <button
                    key={ac}
                    type="button"
                    onClick={() => setLandAcreage(ac)}
                    className={`py-1.5 rounded-xl text-xs font-bold border transition ${
                      landAcreage === ac
                        ? "bg-emerald-600 text-white border-emerald-600"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {ac} Acres
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 5. Language & Consent */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Advisory Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                <option value="mr">मराठी (Marathi - Official)</option>
                <option value="hi">हिंदी (Hindi - Rashtrabhasha)</option>
                <option value="en">English (English)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Sowing / Planting Date
              </label>
              <input
                type="date"
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              />
            </div>
          </div>

          {/* Consent Checkboxes */}
          <div className="space-y-2 pt-1 border-t border-slate-100">
            <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={consentSms}
                onChange={(e) => setConsentSms(e.target.checked)}
                className="w-4 h-4 text-emerald-600 rounded-md border-slate-300 focus:ring-emerald-500"
              />
              <span>I confirm farmer consent for daily plain-language SMS agro-advisories.</span>
            </label>
            <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={consentVoice}
                onChange={(e) => setConsentVoice(e.target.checked)}
                className="w-4 h-4 text-emerald-600 rounded-md border-slate-300 focus:ring-emerald-500"
              />
              <span>I confirm consent for outbound IVR vernacular voice phone calls.</span>
            </label>
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-600/30 transition disabled:opacity-50 cursor-pointer flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{loading ? "Onboarding Farmer..." : "Start Farmer Pipeline"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
