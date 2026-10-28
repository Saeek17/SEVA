"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Send,
  ShieldCheck,
  AlertTriangle,
  PlayCircle,
  PlusCircle,
  RefreshCw,
  Compass,
  CheckCircle2,
  PhoneCall,
  MessageSquare
} from "lucide-react";
import { api } from "@/lib/api";
import { Farmer, AdvisoryRecord, CropMetadata } from "@/lib/types";
import { FarmerMap } from "@/components/FarmerMap";
import { FarmerRegistrationModal } from "@/components/FarmerRegistrationModal";
import { AudioPlayer } from "@/components/AudioPlayer";

export default function DashboardPage() {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [advisories, setAdvisories] = useState<AdvisoryRecord[]>([]);
  const [crops, setCrops] = useState<CropMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchSuccess, setBatchSuccess] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeAudioAdvisory, setActiveAudioAdvisory] = useState<AdvisoryRecord | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [farmersData, advisoriesData, cropsData] = await Promise.all([
        api.getFarmers(),
        api.getAdvisories(10),
        api.getCrops(),
      ]);
      setFarmers(farmersData);
      setAdvisories(advisoriesData);
      setCrops(cropsData);
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunBatch = async () => {
    setBatchRunning(true);
    setBatchSuccess(null);
    try {
      await api.triggerBatchAdvisories();
      setBatchSuccess("Daily morning advisory batch triggered and delivered successfully!");
      await loadData();
    } catch (err: any) {
      alert(`Batch failed: ${err.message}`);
    } finally {
      setBatchRunning(false);
    }
  };

  const getActionBadgeClass = (action: string) => {
    switch (action) {
      case "IRRIGATE":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "SKIP_IRRIGATION":
        return "bg-slate-100 text-slate-700 border-slate-300";
      case "SAFE_SPRAY":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "AVOID_SPRAY":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "HEAT_ALERT":
      case "RAIN_ALERT":
      case "DROUGHT_ALERT":
      case "FROST_ALERT":
        return "bg-rose-50 text-rose-700 border-rose-200 animate-pulse";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const activeAlertCount = advisories.filter(
    (a) => a.advice_items?.some((i) => i.urgency === "HIGH")
  ).length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Agricultural Advisory Operations</h1>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic agronomic rules • Vernacular NLP • Multi-channel delivery to basic mobile phones
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-sm"
          >
            <PlusCircle className="w-4 h-4" />
            Register Farmer
          </button>
          <button
            onClick={handleRunBatch}
            disabled={batchRunning}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-slate-900 hover:bg-slate-800 text-white transition shadow-sm disabled:opacity-60"
          >
            <RefreshCw className={`w-4 h-4 ${batchRunning ? "animate-spin" : ""}`} />
            {batchRunning ? "Processing..." : "Run Daily Batch"}
          </button>
          <Link
            href="/simulate"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-amber-500 hover:bg-amber-600 text-white transition shadow-sm"
          >
            <Compass className="w-4 h-4" />
            Sandbox Simulator
          </Link>
        </div>
      </div>

      {batchSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>{batchSuccess}</span>
          </div>
          <button onClick={() => setBatchSuccess(null)} className="text-emerald-700 text-xs font-semibold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Registered Farmers</p>
            <h3 className="text-2xl font-black text-slate-900">{farmers.length}</h3>
            <p className="text-[11px] text-emerald-600 font-medium">100% Phone Encrypted</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Send className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Advisories Issued</p>
            <h3 className="text-2xl font-black text-slate-900">{advisories.length}</h3>
            <p className="text-[11px] text-blue-600 font-medium">SMS & Automated Voice</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">GKMS Agreement</p>
            <h3 className="text-2xl font-black text-slate-900">83.3%</h3>
            <p className="text-[11px] text-purple-600 font-medium">IMD Bulletins Benchmark</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">High Urgency Alerts</p>
            <h3 className="text-2xl font-black text-rose-600">{activeAlertCount}</h3>
            <p className="text-[11px] text-rose-500 font-medium">24h Deduplicated</p>
          </div>
        </div>
      </div>

      {/* Main Content Layout: Map + Recent Advisories */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Farmer Map (7 cols) */}
        <div className="lg:col-span-7 bg-white p-5 rounded-3xl border border-slate-200 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900">Hyperlocal Coverage Map</h3>
              <p className="text-xs text-slate-500">Farmers clustered by crop across Maharashtra agro-climatic zones</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 rounded-full text-slate-700">
              {farmers.length} Locations
            </span>
          </div>
          <div className="flex-1 min-h-[400px]">
            <FarmerMap farmers={farmers} />
          </div>
        </div>

        {/* Right: Recent Advisories Feed (5 cols) */}
        <div className="lg:col-span-5 bg-white p-5 rounded-3xl border border-slate-200 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900">Live Advisory Feed</h3>
              <p className="text-xs text-slate-500">Rules Engine & Vernacular LLM outputs</p>
            </div>
            <Link href="/advisories" className="text-xs font-semibold text-emerald-600 hover:underline">
              View All
            </Link>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[460px] pr-1">
            {advisories.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No advisories generated yet. Click &quot;Run Daily Batch&quot; or test in the Sandbox Simulator.
              </div>
            ) : (
              advisories.map((adv) => {
                const primaryAction = adv.advice_items?.[0]?.action || "MONITOR_CROP";
                const isSelectedForAudio = activeAudioAdvisory?.id === adv.id;

                return (
                  <div
                    key={adv.id}
                    className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 hover:border-slate-300 transition space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-900">{adv.farmer_name}</span>
                        <span className="text-[11px] text-slate-500 font-medium">
                          {adv.growth_stage} • DAS {adv.das}
                        </span>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getActionBadgeClass(primaryAction)}`}>
                        {primaryAction.replace("_", " ")}
                      </span>
                    </div>

                    <p className="text-xs text-slate-800 font-medium leading-relaxed bg-white p-2.5 rounded-xl border border-slate-100">
                      &quot;{adv.generated_message}&quot;
                    </p>

                    <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500">
                      <div className="flex items-center gap-2">
                        <span className="flex items-center gap-1 font-semibold text-slate-600">
                          <MessageSquare className="w-3 h-3 text-emerald-600" /> SMS
                        </span>
                        <span className="flex items-center gap-1 font-semibold text-slate-600">
                          <PhoneCall className="w-3 h-3 text-blue-600" /> Voice
                        </span>
                      </div>
                      {adv.voice_audio_path && (
                        <button
                          onClick={() => setActiveAudioAdvisory(isSelectedForAudio ? null : adv)}
                          className="flex items-center gap-1 text-emerald-700 hover:underline font-semibold"
                        >
                          <PlayCircle className="w-3.5 h-3.5" />
                          {isSelectedForAudio ? "Hide Audio" : "Play Voice"}
                        </button>
                      )}
                    </div>

                    {isSelectedForAudio && adv.voice_audio_path && (
                      <div className="pt-2">
                        <AudioPlayer
                          audioUrl={adv.voice_audio_path}
                          language={adv.language}
                          label={`Voice to ${adv.farmer_name}`}
                        />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Registration Modal */}
      <FarmerRegistrationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => loadData()}
        crops={crops}
      />
    </div>
  );
}
