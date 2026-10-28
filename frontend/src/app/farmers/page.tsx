"use client";

import { useState, useEffect } from "react";
import {
  Users,
  PlusCircle,
  Search,
  Send,
  UserX,
  CheckCircle2,
  Phone,
  MessageSquare,
  AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";
import { Farmer, CropMetadata } from "@/lib/types";
import { FarmerRegistrationModal } from "@/components/FarmerRegistrationModal";

export default function FarmersPage() {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [crops, setCrops] = useState<CropMetadata[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [cropFilter, setCropFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [farmersData, cropsData] = await Promise.all([
        api.getFarmers(cropFilter || undefined),
        api.getCrops(),
      ]);
      setFarmers(farmersData);
      setCrops(cropsData);
    } catch (err) {
      console.error("Error loading farmers:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [cropFilter]);

  const handleTriggerAdvisory = async (farmer: Farmer) => {
    try {
      const res = await api.triggerFarmerAdvisory(farmer.id);
      setActionSuccess(`Advisory dispatched to ${farmer.full_name} via SMS and Voice!`);
    } catch (err: any) {
      alert(`Trigger failed: ${err.message}`);
    }
  };

  const handleDeactivate = async (farmer: Farmer) => {
    if (!confirm(`Are you sure you want to deactivate farmer ${farmer.full_name}?`)) return;
    try {
      await api.deactivateFarmer(farmer.id);
      setActionSuccess(`Farmer ${farmer.full_name} deactivated (STOP opt-out honored).`);
      await loadData();
    } catch (err: any) {
      alert(`Deactivate failed: ${err.message}`);
    }
  };

  const filteredFarmers = farmers.filter((f) =>
    f.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (f.district && f.district.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Registered Farmers Directory</h1>
          <p className="text-sm text-slate-500 mt-1">
            Compliant with TRAI DLT regulations • Encrypted PII at rest • Direct consent audit trail
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-sm"
        >
          <PlusCircle className="w-4 h-4" />
          Register New Farmer
        </button>
      </div>

      {actionSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-700 text-xs font-semibold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by farmer name or district..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <select
          value={cropFilter}
          onChange={(e) => setCropFilter(e.target.value)}
          className="px-4 py-2 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full sm:w-auto"
        >
          <option value="">All Crops</option>
          {crops.map((c) => (
            <option key={c.crop_id} value={c.crop_id}>
              {c.common_name_en} ({c.common_name_mr})
            </option>
          ))}
        </select>
      </div>

      {/* Farmers Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-xs uppercase font-bold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4">Farmer Details</th>
                <th className="px-6 py-4">Crop & Stage</th>
                <th className="px-6 py-4">Location</th>
                <th className="px-6 py-4">Language</th>
                <th className="px-6 py-4">Consent Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredFarmers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-slate-400">
                    No registered farmers found.
                  </td>
                </tr>
              ) : (
                filteredFarmers.map((f) => {
                  const isWheat = f.crop_id.includes("wheat");
                  return (
                    <tr key={f.id} className="hover:bg-slate-50/70 transition">
                      <td className="px-6 py-4">
                        <div className="font-bold text-slate-900">{f.full_name}</div>
                        <div className="text-xs font-mono text-slate-500">{f.phone_masked}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          isWheat ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"
                        }`}>
                          {isWheat ? "Wheat (गहू)" : "Soybean (सोयाबीन)"}
                        </span>
                        <div className="text-xs text-slate-500 mt-1">Sown: {f.sowing_date}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900">{f.district || "Maharashtra"}</div>
                        <div className="text-xs text-slate-400">
                          {f.latitude.toFixed(2)}°N, {f.longitude.toFixed(2)}°E
                        </div>
                      </td>
                      <td className="px-6 py-4 uppercase font-bold text-xs text-slate-700">
                        {f.language === "mr" ? "Marathi" : f.language === "hi" ? "Hindi" : "English"}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-xs text-slate-600">
                          <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
                          <span>SMS</span>
                          <span className="text-slate-300">•</span>
                          <Phone className="w-3.5 h-3.5 text-blue-600" />
                          <span>Voice</span>
                        </div>
                        {f.is_active ? (
                          <span className="inline-block mt-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                            Active
                          </span>
                        ) : (
                          <span className="inline-block mt-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md">
                            Opted Out (STOP)
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleTriggerAdvisory(f)}
                            className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition"
                            title="Trigger Advisory Now"
                          >
                            <Send className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeactivate(f)}
                            className="p-1.5 rounded-lg bg-slate-50 text-slate-500 hover:bg-red-50 hover:text-red-700 transition"
                            title="Deactivate / Honor Opt-Out"
                          >
                            <UserX className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <FarmerRegistrationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => loadData()}
        crops={crops}
      />
    </div>
  );
}
