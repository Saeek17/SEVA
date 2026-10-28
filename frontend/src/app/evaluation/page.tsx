"use client";

import { useState, useEffect } from "react";
import {
  ShieldCheck,
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Calendar,
  FileSpreadsheet,
  FileText
} from "lucide-react";
import { api } from "@/lib/api";
import { EvaluationResult } from "@/lib/types";

export default function EvaluationPage() {
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoaded, setInitialLoaded] = useState(false);

  const runEvaluation = async () => {
    setLoading(true);
    try {
      const data = await api.runEvaluation();
      setEvalResult(data);
    } catch (err: any) {
      alert(`Evaluation failed: ${err.message}`);
    } finally {
      setLoading(false);
      setInitialLoaded(true);
    }
  };

  useEffect(() => {
    runEvaluation();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                GKMS Advisory Benchmark Evaluation
              </h1>
              <p className="text-sm text-slate-500">
                Ground-truth validation against official IMD Gramin Krishi Mausam Sewa district bulletins.
              </p>
            </div>
          </div>
        </div>
        <button
          onClick={runEvaluation}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-sm disabled:opacity-60"
        >
          <Play className={`w-4 h-4 fill-current ${loading ? "animate-spin" : ""}`} />
          {loading ? "Evaluating..." : "Run Evaluation Suite"}
        </button>
      </div>

      {evalResult && (
        <>
          {/* Agreement KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Overall Exact Agreement
              </span>
              <h3 className="text-3xl font-black text-slate-900 mt-1">
                {evalResult.overall_exact_agreement_pct}%
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                {evalResult.total_evaluated} official agromet bulletins
              </p>
            </div>

            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Irrigation Agreement
              </span>
              <h3 className="text-3xl font-black text-blue-600 mt-1">
                {evalResult.irrigation_agreement_pct}%
              </h3>
              <p className="text-[11px] text-blue-500 mt-1">
                Irrigate vs Skip Irrigation
              </p>
            </div>

            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Spraying Agreement
              </span>
              <h3 className="text-3xl font-black text-emerald-600 mt-1">
                {evalResult.spraying_agreement_pct}%
              </h3>
              <p className="text-[11px] text-emerald-500 mt-1">
                Safe Window vs Avoid Spray
              </p>
            </div>

            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Hazard Alert Agreement
              </span>
              <h3 className="text-3xl font-black text-amber-600 mt-1">
                {evalResult.alert_agreement_pct}%
              </h3>
              <p className="text-[11px] text-amber-500 mt-1">
                Rain, Heat & Drought Alerts
              </p>
            </div>
          </div>

          {/* Detailed Benchmark Agreement Table */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900">Ground-Truth Agreement Table</h3>
                <p className="text-xs text-slate-500">
                  Itemized comparison between human expert advisory and KisanSaathi deterministic rules engine
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 rounded-full text-slate-700">
                {evalResult.records?.length || 0} Evaluated Records
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-xs uppercase font-bold text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-5 py-3.5">Bulletin & District</th>
                    <th className="px-5 py-3.5">Crop & Stage</th>
                    <th className="px-5 py-3.5">Expert Recommendation</th>
                    <th className="px-5 py-3.5">KisanSaathi Decision</th>
                    <th className="px-5 py-3.5 text-center">Agreement</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {evalResult.records?.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-50/70 transition">
                      <td className="px-5 py-3.5">
                        <div className="font-bold text-slate-900">{rec.district}</div>
                        <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                          <Calendar className="w-3 h-3 text-slate-400" /> {rec.bulletin_date}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono truncate max-w-[200px]">
                          {rec.source_bulletin}
                        </div>
                      </td>

                      <td className="px-5 py-3.5">
                        <div className="font-bold text-slate-900">{rec.crop_name}</div>
                        <div className="text-slate-500">{rec.growth_stage}</div>
                        <div className="text-[10px] text-slate-400">DAS: {rec.das}</div>
                      </td>

                      <td className="px-5 py-3.5 space-y-1">
                        <div>
                          <strong>Irrigation:</strong>{" "}
                          <span className="font-semibold text-slate-900">{rec.expert_advice.irrigation}</span>
                        </div>
                        <div>
                          <strong>Spray:</strong>{" "}
                          <span className="font-semibold text-slate-900">{rec.expert_advice.spray}</span>
                        </div>
                        {rec.expert_advice.alert !== "NONE" && (
                          <div className="text-rose-600 font-bold">Alert: {rec.expert_advice.alert}</div>
                        )}
                        <p className="text-[11px] text-slate-500 italic mt-1 max-w-sm">
                          &quot;{rec.expert_advice.expert_summary_en}&quot;
                        </p>
                      </td>

                      <td className="px-5 py-3.5 space-y-1">
                        <div>
                          <strong>Irrigation:</strong>{" "}
                          <span className={rec.agreement.irrigation ? "text-emerald-700 font-bold" : "text-rose-600 font-bold"}>
                            {rec.system_advice.irrigation}
                          </span>
                        </div>
                        <div>
                          <strong>Spray:</strong>{" "}
                          <span className={rec.agreement.spray ? "text-emerald-700 font-bold" : "text-rose-600 font-bold"}>
                            {rec.system_advice.spray}
                          </span>
                        </div>
                        {rec.system_advice.alert !== "NONE" && (
                          <div className="text-rose-600 font-bold">Alert: {rec.system_advice.alert}</div>
                        )}
                      </td>

                      <td className="px-5 py-3.5 text-center">
                        {rec.agreement.overall ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Exact Match
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                            <AlertTriangle className="w-3.5 h-3.5" /> Discrepancy
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mismatch Manual Review Box */}
          {evalResult.mismatches && evalResult.mismatches.length > 0 && (
            <div className="bg-amber-50/50 p-6 rounded-3xl border border-amber-200 shadow-xs space-y-3">
              <div className="flex items-center gap-2 text-amber-900 font-bold">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <span>Discrepancy Inspector for Agronomic Expert Calibration</span>
              </div>
              <p className="text-xs text-amber-800 leading-relaxed">
                The following {evalResult.mismatches.length} records generated decisions different from the official bulletin.
                Agronomists can review these cases to calibrate thresholds in <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">/config/crops/*.yaml</code>:
              </p>

              <div className="space-y-2 pt-2">
                {evalResult.mismatches.map((m) => (
                  <div key={m.id} className="p-3.5 rounded-2xl bg-white border border-amber-200 text-xs space-y-1">
                    <div className="flex justify-between font-bold text-slate-900">
                      <span>{m.district} • {m.crop_name}</span>
                      <span className="text-slate-500 font-normal">{m.bulletin_date}</span>
                    </div>
                    <div className="text-slate-600">
                      <strong>Disagreements:</strong> {JSON.stringify(m.disagreements)}
                    </div>
                    <div className="text-slate-500 italic mt-1">
                      <strong>Expert Bulletin:</strong> &quot;{m.expert_summary}&quot;
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dataset Attribution Box */}
          <div className="p-4 rounded-2xl bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-800">Benchmark Attribution & Ground Truth Policy</p>
              <p className="mt-0.5 text-slate-500">
                Bulletins are official publications of the India Meteorological Department (IMD) Gramin Krishi Mausam Sewa (GKMS)
                and State Agricultural Universities (MPKV Rahuri, VNMKV Parbhani, PDKV Akola). No benchmark data is fabricated.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
