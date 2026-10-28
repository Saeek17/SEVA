# Inputs Needed From User: KisanSaathi

To transition KisanSaathi from local demonstration and mock dry-run mode to full production deployment, the following external keys, files, and decisions are required.

> **Current Operational Status:**  
> Until these credentials and files are provided, the system runs safely in **MOCK / DRY-RUN mode (`DRY_RUN=true`)**. In this mode:
> - Weather & Soil APIs (Open-Meteo, NASA POWER, ISRIC SoilGrids) make **real HTTP calls** (they require **zero API keys**).
> - Gemini LLM operates with offline rule-template generation or mock vernacular phrasing when `GEMINI_API_KEY` is empty.
> - Voice synthesizes local WAV audio via Python `wave` module when Google Cloud TTS credentials are empty.
> - SMS and Voice dispatches log simulated SIDs and payloads rather than incurring telecom carrier charges.

---

## 1. External API Keys & Accounts

All environment variables must be placed into your local `.env` file in the root workspace directory (see `.env.example`).

| Variable Name | Description | Where It Goes | Where to Obtain | Required For |
| :--- | :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini AI API key | Root `.env` | [Google AI Studio](https://aistudio.google.com/) | Vernacular phrasing of advice (<320 chars SMS). Optional; defaults to certified DLT templates if missing. |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Root `.env` | [Twilio Console](https://console.twilio.com/) | Real outbound SMS, WhatsApp, and Voice calls. |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Root `.env` | [Twilio Console](https://console.twilio.com/) | Twilio API authentication. |
| `TWILIO_FROM_PHONE` | Twilio Phone Number | Root `.env` | Twilio Phone Numbers | Sender phone number (E.164 format, e.g. `+15005550006`). |
| `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp Sandbox Number | Root `.env` | Twilio Messaging Sandbox | Outbound WhatsApp messages. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Absolute path to Google Cloud Service Account JSON | Root `.env` | [Google Cloud Console](https://console.cloud.google.com/) (Text-to-Speech API) | High-fidelity neural voice synthesis (Hindi `hi-IN-Neural2-B`, Marathi `mr-IN-Wavenet-A`). Falls back to local WAV if blank. |
| `DATABASE_URL` | PostgreSQL connection string | Root `.env` | [Supabase](https://supabase.com/) or local Postgres | Production multi-user database. Optional: defaults to local zero-config SQLite (`sqlite:///./kisansaathi.db`). |
| `DATA_GOV_IN_API_KEY` | data.gov.in API Key | Root `.env` | [data.gov.in](https://data.gov.in/) | **Phase 2 only:** Real-time Agmarknet mandi crop prices and historical KCC query datasets. |

---

## 2. Benchmark & Knowledge Base Files

Place these files in the respective directories when available:

### A. Real IMD GKMS Advisories
- **Target Directory:** `data/benchmarks/gkms_advisories.json`
- **Purpose:** Used by the evaluation harness to benchmark KisanSaathi rules against official IMD District Agromet Bulletins.
- **Expected JSON Schema:**
```json
[
  {
    "id": "GKMS-MH-PUN-2023-11-24",
    "district": "Pune",
    "state": "Maharashtra",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "bulletin_date": "2023-11-24",
    "crop_id": "wheat_maharashtra",
    "crop_name": "Wheat",
    "growth_stage": "Crown Root Initiation (CRI)",
    "das": 21,
    "source_bulletin": "IMD Pune GKMS Agromet Advisory Bulletin No. 94/2023",
    "observed_conditions": {
      "forecast_rain_48h_mm": 0.0,
      "max_temp_c": 29.5,
      "min_temp_c": 14.2,
      "wind_speed_kmh": 8.0,
      "soil_moisture_pct": 28.0
    },
    "expert_advice": {
      "irrigation": "IRRIGATE",
      "spray": "SAFE_SPRAY",
      "alert": "NONE",
      "expert_summary_en": "Official advisory text snippet..."
    }
  }
]
```

### B. Agricultural University Package of Practices (PoP) PDFs
- **Target Directory:** `data/knowledge/`
- **Files:** Official PDFs from MPKV Rahuri, VNMKV Parbhani, PDKV Akola, or ICAR institutes.
- **Purpose:** Source of truth for validating crop thresholds in `config/crops/*.yaml` and removing `# NEEDS_EXPERT_REVIEW` tags.

---

## 3. Decisions Confirmed & Defaults in Place

1. **Target Agricultural State & Districts:**
   - **Default Configured:** Maharashtra (Nashik, Latur, Pune, Ahmednagar, Akola).
   - *Status:* Supported out of the box.
2. **Target Crops:**
   - **Crop 1:** Wheat (`wheat_maharashtra.yaml`) citing MPKV Rahuri PoP.
   - **Crop 2:** Soybean (`soybean_maharashtra.yaml`) citing VNMKV Parbhani PoP.
   - *Status:* Fully implemented and validated against `config/crops/schema.json`.
3. **Languages Supported:**
   - English (`en`), Hindi (`hi`), Marathi (`mr`).
   - *Status:* Certified DLT templates and AI4Bharat/Bhashini agricultural glossaries populated in `data/language/`.
