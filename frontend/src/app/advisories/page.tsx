"use client";

import { useState, useEffect } from "react";
import {
  FileCheck2,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  Phone,
  MessageSquare,
  ShieldCheck,
  XCircle,
  Database,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";
import { AdvisoryRecord } from "@/lib/types";
import { AudioPlayer } from "@/components/AudioPlayer";

export default function AdvisoriesPage() {
  const [advisories, setAdvisories] = useState<AdvisoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeAudioId, setActiveAudioId] = useState<string | null>(null);

  useEffect(() => {
    api.getAdvisories(50).then(setAdvisories).finally(() => setLoading(false));
  }, []);

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
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
            <FileCheck2 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Advisory Audit & Trace History</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Side-by-side comparison: Deterministic Rules decisions vs LLM Vernacular Phrasing & Delivery Telemetry.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Loading advisory audit log...</div>
      ) : advisories.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 text-slate-400 text-sm">
          No advisory records found. Run the Daily Batch on the Dashboard or simulate on the Simulator page.
        </div>
      ) : (
        <div className="space-y-4">
          {advisories.map((adv) => {
            const isPlayingAudio = activeAudioId === adv.id;

            return (
              <div
                key={adv.id}
                className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4 hover:border-slate-300 transition"
              >
                {/* Meta header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-900 text-base">{adv.farmer_name}</span>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                      {adv.crop_id.replace("_maharashtra", "")} • {adv.growth_stage} (DAS {adv.das})
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>{new Date(adv.created_at).toLocaleString()}</span>
                    <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                      Confidence: {adv.data_confidence}
                    </span>
                  </div>
                </div>

                {/* 3-Column Side-by-Side Audit Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                  {/* Col 1: Structured Advice Items (5 cols) */}
                  <div className="lg:col-span-5 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        1. Structured Advice Items (Rules Engine)
                      </span>
                    </div>

                    <div className="space-y-2">
                      {adv.advice_items?.map((item, idx) => (
                        <div key={idx} className="p-2.5 rounded-xl bg-white border border-slate-200 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className={`text-[11px] font-black px-2 py-0.5 rounded-full border ${getActionBadgeColor(item.action)}`}>
                              {item.action}
                            </span>
                            <span className="text-[10px] font-bold text-slate-500 uppercase">
                              {item.urgency}
                            </span>
                          </div>
                          <div className="font-mono text-[11px] text-slate-700">{item.reason_code}</div>
                          <div className="text-[11px] text-slate-500">
                            <strong>Params:</strong> {JSON.stringify(item.params)}
                          </div>
                          {item.source_citation && (
                            <div className="text-[10px] text-slate-400">
                              <strong>Source:</strong> {item.source_citation}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Col 2: LLM Vernacular Message (4 cols) */}
                  <div className="lg:col-span-4 p-4 rounded-2xl bg-slate-900 text-white shadow-xs space-y-2.5 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                        <span className="font-bold uppercase tracking-wider text-slate-300">
                          2. Generated Vernacular Message
                        </span>
                        <span className="uppercase text-[10px] px-1.5 py-0.5 rounded-md bg-slate-800 text-slate-300">
                          {adv.language}
                        </span>
                      </div>
                      <p className="text-xs text-slate-100 font-medium leading-relaxed bg-slate-800/80 p-3 rounded-xl border border-slate-700">
                        &quot;{adv.generated_message}&quot;
                      </p>
                    </div>

                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400">Length: {adv.generated_message.length} / 320 chars</span>
                        {adv.validation_passed ? (
                          <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Guardrail Passed
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-amber-400 font-semibold">
                            <XCircle className="w-3.5 h-3.5" /> DLT Fallback
                          </span>
                        )}
                      </div>

                      {adv.voice_audio_path && (
                        <button
                          onClick={() => setActiveAudioId(isPlayingAudio ? null : adv.id)}
                          className="w-full py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 transition"
                        >
                          <PlayCircle className="w-3.5 h-3.5 fill-current" />
                          {isPlayingAudio ? "Hide Voice Audio" : "Listen to Voice Audio"}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Col 3: Delivery Telemetry (3 cols) */}
                  <div className="lg:col-span-3 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                      3. Delivery Telemetry
                    </span>

                    <div className="space-y-2">
                      {adv.delivery_logs?.map((dl, idx) => (
                        <div key={idx} className="p-2 rounded-xl bg-white border border-slate-200 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-800 flex items-center gap-1">
                              {dl.channel === "SMS" ? <MessageSquare className="w-3 h-3 text-emerald-600" /> : <Phone className="w-3 h-3 text-blue-600" />}
                              {dl.channel}
                            </span>
                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
                              {dl.status}
                            </span>
                          </div>
                          <div className="font-mono text-[10px] text-slate-500 truncate">
                            SID: {dl.external_sid || "MOCK_SID"}
                          </div>
                          <div className="text-[10px] text-slate-400">Provider: {dl.provider}</div>
                        </div>
                      ))}
                    </div>

                    <div className="pt-1 text-[11px] text-slate-400">
                      <strong>Sources:</strong> {adv.sources_used}
                    </div>
                  </div>
                </div>

                {/* Inline Audio Player Dropdown */}
                {isPlayingAudio && adv.voice_audio_path && (
                  <div className="pt-2">
                    <AudioPlayer
                      audioUrl={adv.voice_audio_path}
                      language={adv.language}
                      label={`Voice Call Audio for ${adv.farmer_name}`}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
