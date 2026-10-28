import {
  CropMetadata,
  Farmer,
  AdvisoryRecord,
  SimulationResult,
  EvaluationResult
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = "API Request failed";
    try {
      const err = await res.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return handleResponse<any>(res);
  },

  // Crops (dynamically discovered)
  async getCrops(): Promise<CropMetadata[]> {
    const res = await fetch(`${API_BASE}/crops`, { cache: "no-store" });
    return handleResponse<CropMetadata[]>(res);
  },

  async getCropDetail(cropId: string) {
    const res = await fetch(`${API_BASE}/crops/${cropId}`, { cache: "no-store" });
    return handleResponse<any>(res);
  },

  async getCropStage(cropId: string, das: number) {
    const res = await fetch(`${API_BASE}/crops/${cropId}/stage/${das}`, { cache: "no-store" });
    return handleResponse<any>(res);
  },

  // Farmers
  async getFarmers(cropId?: string, isActive?: boolean): Promise<Farmer[]> {
    let url = `${API_BASE}/farmers`;
    const params = new URLSearchParams();
    if (cropId) params.append("crop_id", cropId);
    if (isActive !== undefined) params.append("is_active", String(isActive));
    if (params.toString()) url += `?${params.toString()}`;

    const res = await fetch(url, { cache: "no-store" });
    return handleResponse<Farmer[]>(res);
  },

  async registerFarmer(data: {
    full_name: string;
    phone_number: string;
    language: string;
    latitude: number;
    longitude: number;
    district?: string;
    crop_id: string;
    sowing_date: string;
    consent_sms: boolean;
    consent_voice: boolean;
  }): Promise<Farmer> {
    const res = await fetch(`${API_BASE}/farmers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    return handleResponse<Farmer>(res);
  },

  async deactivateFarmer(farmerId: string) {
    const res = await fetch(`${API_BASE}/farmers/${farmerId}`, {
      method: "DELETE"
    });
    return handleResponse<any>(res);
  },

  // Advisories
  async getAdvisories(limit = 50, farmerId?: string): Promise<AdvisoryRecord[]> {
    let url = `${API_BASE}/advisories?limit=${limit}`;
    if (farmerId) url += `&farmer_id=${farmerId}`;
    const res = await fetch(url, { cache: "no-store" });
    return handleResponse<AdvisoryRecord[]>(res);
  },

  async triggerBatchAdvisories() {
    const res = await fetch(`${API_BASE}/advisories/run-batch`, {
      method: "POST"
    });
    return handleResponse<any>(res);
  },

  async triggerFarmerAdvisory(farmerId: string) {
    const res = await fetch(`${API_BASE}/advisories/farmer/${farmerId}/trigger`, {
      method: "POST"
    });
    return handleResponse<any>(res);
  },

  // Sandbox Simulator
  async simulateFarmer(payload: {
    latitude: number;
    longitude: number;
    crop_id: string;
    das?: number;
    sowing_date?: string;
    language: string;
    farmer_name?: string;
  }): Promise<SimulationResult> {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return handleResponse<SimulationResult>(res);
  },

  // GKMS Benchmark Evaluation
  async runEvaluation(): Promise<EvaluationResult> {
    const res = await fetch(`${API_BASE}/evaluation/run`, { cache: "no-store" });
    return handleResponse<EvaluationResult>(res);
  },

  async getBenchmarks() {
    const res = await fetch(`${API_BASE}/evaluation/benchmarks`, { cache: "no-store" });
    return handleResponse<any>(res);
  }
};
