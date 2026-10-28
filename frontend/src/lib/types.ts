export interface CropMetadata {
  crop_id: string;
  common_name_en: string;
  common_name_hi: string;
  common_name_mr: string;
  scientific_name: string;
  typical_duration_days: number;
  region: string;
  stage_count: number;
}

export interface GrowthStage {
  stage_id: string;
  name_en: string;
  name_hi: string;
  name_mr: string;
  das_start: number;
  das_end: number;
  critical_for_irrigation: boolean;
  critical_reason?: string;
}

export interface EnvironmentalSnapshot {
  latitude: number;
  longitude: number;
  forecast_max_temp_c: number;
  forecast_min_temp_c: number;
  forecast_rain_24h_mm: number;
  forecast_rain_48h_mm: number;
  forecast_rain_7d_mm: number;
  rain_probability_pct: number;
  wind_speed_kmh: number;
  relative_humidity_pct: number;
  soil_moisture_0_7cm_pct: number;
  soil_moisture_7_28cm_pct: number;
  soil_temp_0_7cm_c: number;
  soil_texture_class: string;
  consecutive_dry_days: number;
  cumulative_rain_30d_mm: number;
  data_confidence: "HIGH" | "MEDIUM" | "LOW";
  sources_used: string[];
}

export interface AdviceItem {
  action: "IRRIGATE" | "SKIP_IRRIGATION" | "SCHEDULE_IRRIGATION" | "SAFE_SPRAY" | "AVOID_SPRAY" | "HEAT_ALERT" | "FROST_ALERT" | "RAIN_ALERT" | "DROUGHT_ALERT" | "HARVEST_READY" | "MONITOR_CROP";
  urgency: "HIGH" | "MEDIUM" | "LOW";
  reason_code: string;
  params: Record<string, any>;
  data_confidence: string;
  sources_used: string[];
  source_citation?: string;
  priority_rank?: number;
}

export interface SimulationResult {
  status: string;
  crop_id: string;
  crop_name: string;
  growth_stage: string;
  das: number;
  environmental_data: EnvironmentalSnapshot;
  advice_items: AdviceItem[];
  generated_message: string;
  language: string;
  validation_passed: boolean;
  validation_notes?: string;
  fallback_used: string;
  voice_audio_url?: string;
}

export interface Farmer {
  id: string;
  full_name: string;
  phone_masked: string;
  language: "hi" | "mr" | "en";
  latitude: number;
  longitude: number;
  district?: string;
  state: string;
  crop_id: string;
  sowing_date: string;
  consent_sms: boolean;
  consent_voice: boolean;
  is_active: boolean;
  created_at: string;
}

export interface DeliveryLog {
  channel: "SMS" | "VOICE";
  provider: string;
  status: string;
  external_sid?: string;
  dispatched_at: string;
}

export interface AdvisoryRecord {
  id: string;
  farmer_id?: string;
  farmer_name?: string;
  crop_id: string;
  growth_stage: string;
  das: number;
  data_confidence: string;
  sources_used: string;
  generated_message: string;
  language: string;
  validation_passed: boolean;
  validation_notes?: string;
  fallback_used: string;
  voice_audio_path?: string;
  created_at: string;
  advice_items: AdviceItem[];
  delivery_logs: DeliveryLog[];
}

export interface EvaluationResult {
  status: string;
  total_evaluated: number;
  overall_exact_agreement_pct: number;
  irrigation_agreement_pct: number;
  spraying_agreement_pct: number;
  alert_agreement_pct: number;
  records: any[];
  mismatches: any[];
}
