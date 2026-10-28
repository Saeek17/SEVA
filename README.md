# KisanSaathi (किसान साथी)
### Hyperlocal, Actionable, Vernacular Agro-Advisory Engine for Smallholder Farmers

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%20App%20Router-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-blue.svg)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://www.python.org)
[![TailwindCSS](https://img.shields.io/badge/Styling-TailwindCSS-38B2AC.svg)](https://tailwindcss.com)
[![Tests](https://img.shields.io/badge/Tests-31%20Passed-brightgreen.svg)]()

---

## 1. Problem Statement & Core Philosophy

Smallholder farmers across rural India face severe yield losses due to erratic climate shocks (terminal heat waves, unseasonal rainfall, prolonged dry spells, high winds causing spray drift) and lack usable, crop-stage-specific guidance in their native language. Existing smartphone apps fail to reach the most vulnerable farmers who rely on basic feature phones (2G/3G) with no internet access.

**KisanSaathi** solves this by delivering hyperlocal, actionable, crop-stage-specific agricultural guidance directly to ordinary mobile phones via standard **SMS** and automated outbound **Voice Calls (TTS)** in **Hindi**, **Marathi**, and **English**.

### Immutable Design Principles
1. **Zero LLM Agronomic Authority**: A Generative AI model must **NEVER** decide agricultural actions, chemical dosages, or irrigation timings. All agronomic decisions are derived by a strictly deterministic, explainable Rules Engine reading expert-cited crop configuration files.
2. **Generative AI as Vernacular Scribe Only**: The Large Language Model (Gemini API) is employed purely to translate and summarize structured advice objects into empathetic, simple, high-impact SMS text (<320 characters) and voice scripts.
3. **Rigid Output Guardrails & DLT Template Fallback**: Every generated message undergoes algorithmic AST/regex validation. If an unapproved action (e.g. recommending "pesticide spray" when only irrigation advice was produced) or mismatched numerical quantity is detected, the system immediately drops the LLM response and falls back to pre-certified, TRAI DLT-compliant message templates.
4. **Dynamic Configuration Driven**: No crop names, growth stages, or agro-climatic thresholds may be hardcoded. Crops are defined strictly in `/config/crops/*.yaml` and discovered dynamically by the backend, registration form, and sandbox simulator. Adding a new crop requires only adding a new YAML file.
5. **Full Explainability & Auditability**: Every advice item is linked to a reason code, parameter dictionary, data confidence score, and specific State Agricultural University (MPKV Rahuri, VNMKV Parbhani, PDKV Akola) or ICAR source citations marked with `# NEEDS_EXPERT_REVIEW`.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph External_Data [Hyperlocal Environmental Facts]
        OM[Open-Meteo API\n7-Day Forecast & Soil Moisture]
        NP[NASA POWER API\n30-Day Rain & Dry Spell History]
        SG[ISRIC SoilGrids 250m\nSoil Texture Classification]
    end

    subgraph Core_Backend [FastAPI Backend Service]
        Agg[Data Aggregator & TTL Cache]
        CropLoader[Dynamic Crop Config Loader\n/config/crops/*.yaml]
        DAS[Stage Calculator\nDays After Sowing &rarr; Stage]
        Rules[Deterministic Rules Engine\nIrrigation, Spray, Alerts, Harvest]
        
        LLM[Gemini Vernacular Scribe\nGKMS Few-Shot Prompt Builder]
        Guardrail[Anti-Hallucination Guardrail\nAction Whitelist & Numeric Fidelity]
        DLT[Certified DLT Template Fallback\nHindi / Marathi / English]
    end

    subgraph Multi_Channel_Delivery [Farmer Communication Channels]
        TwilioSMS[Twilio / Exotel SMS\nStandard Text &lt;320 chars]
        TwilioVoice[Outbound Voice Call\nGoogle Cloud Text-to-Speech]
        OptOut[Inbound STOP Webhook\nAuto Opt-Out & Consent Ledger]
    end

    subgraph Admin_Interface [Next.js App Router Frontend]
        Dash[Operations Dashboard & Leaflet Map]
        Sim[Live Sandbox Simulator]
        Audit[Advisory Trace History]
        Eval[GKMS Benchmark Evaluation]
    end

    OM --> Agg
    NP --> Agg
    SG --> Agg

    Agg --> Rules
    CropLoader --> DAS
    DAS --> Rules
    Rules -->|Structured Advice Items| LLM
    LLM --> Guardrail
    Guardrail -- Passed --> TwilioSMS
    Guardrail -- Passed --> TwilioVoice
    Guardrail -- Rejected --> DLT --> TwilioSMS
    Guardrail -- Rejected --> DLT --> TwilioVoice

    TwilioSMS --> OptOut
    TwilioVoice --> OptOut

    Core_Backend <--> Admin_Interface
```

---

## 3. Environmental Data Sources & Attribution

> [!NOTE]
> **Scientific Accuracy Notice**: The environmental APIs utilized below are **model-reanalysis and satellite-assimilated gridded products**, not raw satellite imagery. They provide continuous, calibrated estimates at farmer coordinates.

| Data Source | What It Provides | Spatial & Temporal Resolution | License & Terms | Attribution Requirements |
|---|---|---|---|---|
| **Open-Meteo API** | 7-day weather forecast (temp, rain, wind, RH), multi-depth soil moisture (0-7cm, 7-28cm), and soil temperature | Hourly & Daily; ~1 km to 11 km grid | Non-commercial & Open Data (CC-BY-4.0) | "Weather data by Open-Meteo.com" |
| **NASA POWER API** | Last 30 days daily precipitation and temperature history for exact lat/lon; used for consecutive dry spell & cumulative rain checks | Daily point queries; 0.5° x 0.5° assimilation | Public Domain (NASA Open Data Policy) | "Data courtesy of NASA Langley Research Center POWER Project" |
| **ISRIC SoilGrids 2.0** | Clay, sand, and silt percentages at depths; derived USDA soil texture class (e.g., Clay Loam / Black Cotton Soil) | 250 m global spatial grid; static | Creative Commons Attribution 4.0 (CC-BY-4.0) | "Soil data derived from ISRIC SoilGrids 250m" |
| **IMD GKMS Bulletins** | Historical expert district agromet advisories used as ground-truth evaluation benchmark and few-shot examples | District-level; Bi-weekly (Tuesdays & Fridays) | Government Open Data License - India (GODL-India) | "Data courtesy of India Meteorological Department (IMD), Ministry of Earth Sciences" |
| **Kisan Call Centre (KCC)** | Anonymized query logs from farmers across Maharashtra on data.gov.in; informs real farmer question intents | Point call records | Government Open Data License - India (GODL-India) | "Department of Agriculture & Farmers Welfare, Ministry of Agriculture and Farmers Welfare" |
| **AI4Bharat & Bhashini** | Agricultural vernacular terms and translations in Hindi and Marathi | Linguistic glossaries | Creative Commons Attribution 4.0 (CC-BY-4.0) | "AI4Bharat, IIT Madras & Digital India Bhashini" |

---

## 4. Crop Configuration Knowledge Base (`/config/crops/`)

Every crop configuration is a self-contained YAML document. **No crop names, growth stages, or agro-climatic thresholds may be hardcoded anywhere in application code.**

### Shipped Crop Configurations
1. **Rabi Wheat (`wheat_maharashtra.yaml`)**:
   - Encodes MPKV Rahuri *Package of Practices for Rabi Crops* (pp. 38–46) and ICAR-IIWBR guidelines.
   - Growth stages: Crown Root Initiation (CRI), Tillering, Late Jointing & Flowering, Milking & Dough, Maturity.
   - Stage-by-stage soil moisture depletion triggers (35% at CRI, 40% at tillering), heat stress limits (34°C at flowering, 35°C terminal), and wind drift limits (12 km/h).
2. **Kharif Soybean (`soybean_maharashtra.yaml`)**:
   - Encodes VNMKV Parbhani *Package of Practices for Kharif Crops* and ICAR-IISR Indore Technical Bulletin No. 58.
   - Growth stages: Germination & Seedling, Vegetative Branching, Flowering, Pod Development & Seed Fill, Maturity.
   - Stage-by-stage waterlogging thresholds, pod fill moisture triggers (45%), and pre-harvest interval (PHI) chemical restrictions.

### Agronomy Citation & Expert Review Protocol
- Every threshold in a crop config has a `source` field citing the specific document and page.
- Every unverified threshold includes a `# NEEDS_EXPERT_REVIEW` comment.
- If a citation is not definitively validated, it is designated as `"SOURCE_TBD"`. Never invent or fabricate agronomic citations.

---

## 5. Telecom Compliance & TRAI DLT Regulations (India)

Commercial and transactional SMS messaging in India is governed by TRAI's **Telecom Commercial Communications Customer Preference Regulations (TCCCPR, 2018)** using Distributed Ledger Technology (DLT).

### DLT Registration Requirements
1. **Principal Entity (PE) Registration**: KisanSaathi must be registered as a PE on telecom operator DLT portals (e.g. Jio, Airtel, Vodafone Idea, BSNL).
2. **Sender ID (Header)**: Requires an approved 6-character alphabetic sender ID (e.g. `KSATHI` or `KISANX`).
3. **Template Registration**: Every SMS format must be registered with fixed text and variable parameters `{#var#}`.
4. **Certified DLT Templates (`/data/language/dlt_templates.json`)**:
   KisanSaathi ships with certified DLT templates in Hindi, Marathi, and English for:
   - `IRRIGATE` (`DLT-KS-IRR-01`)
   - `SKIP_IRRIGATION` (`DLT-KS-SKP-01`)
   - `SAFE_SPRAY` (`DLT-KS-SPR-01`)
   - `AVOID_SPRAY` (`DLT-KS-SPR-02`)
   - `HEAT_ALERT` (`DLT-KS-ALT-01`)
   - `RAIN_ALERT` (`DLT-KS-ALT-02`)
   - `DROUGHT_ALERT` (`DLT-KS-ALT-03`)
   - `HARVEST_READY` (`DLT-KS-HRV-01`)
5. **Opt-Out & Privacy**:
   - Inbound SMS webhook listens for `"STOP"`, `"UNSUBSCRIBE"`, or vernacular equivalents (`"थांबवा"`, `"रोकें"`).
   - Receiving an opt-out automatically flips `farmer.is_active = False` in the database, halting all automated SMS and phone calls.
   - Phone numbers are encrypted symmetrically at rest using **Fernet AES-256** with an indexed HMAC-SHA256 hash for fast exact lookups without decrypting.

---

## 6. GKMS Ground-Truth Evaluation Harness

The system includes an automated evaluation harness located at `backend/app/services/evaluation/gkms_evaluator.py` and visual dashboard at `/evaluation`.

- **Benchmark Dataset**: Real historical district agromet advisory bulletins issued by IMD Gramin Krishi Mausam Sewa (GKMS) stored in `/data/benchmarks/gkms_advisories.json`.
- **Methodology**:
  1. Loads each historical bulletin record with recorded weather, crop stage, and expert agronomist recommendations.
  2. Runs KisanSaathi's deterministic rules engine against those exact weather and soil facts.
  3. Computes:
     - **Overall Exact Agreement %**: Where all key decisions (irrigate, spray, alert) matched the expert.
     - **Irrigation Agreement %**: Agreement on `IRRIGATE` vs `SKIP_IRRIGATION`.
     - **Spraying Agreement %**: Agreement on `SAFE_SPRAY` vs `AVOID_SPRAY`.
     - **Alert Agreement %**: Agreement on `RAIN_ALERT`, `HEAT_ALERT`, or `NONE`.
  4. Automatically isolates and lists **mismatches** with full meteorological context for expert agronomist review.

---

## 7. Quickstart & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20 / 22 recommended)
- Docker & Docker Compose (optional for containerized deployment)

### Option A: Local Native Setup

#### 1. Clone & Setup Environment
```bash
cp .env.example .env
```

#### 2. Backend Setup (FastAPI)
```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# Run full unit test suite (31 tests):
pytest

# Start FastAPI dev server on port 8000:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
FastAPI documentation will be available at: `http://localhost:8000/docs`

#### 3. Frontend Setup (Next.js)
```bash
cd ../frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

### Option B: Docker Compose Deployment

Run the complete stack (PostgreSQL + FastAPI + Next.js) with one command:
```bash
docker-compose up --build
```
- Web Dashboard: `http://localhost:3000`
- FastAPI Endpoints: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## 8. Verification & Demo Walkthrough

1. **Operations Dashboard (`/dashboard`)**:
   - Inspect active farmer counts, SMS/voice advisories issued, and GKMS agreement score.
   - View the interactive Leaflet map of Maharashtra with pins color-coded by crop (Amber = Wheat, Emerald = Soybean).
   - Click **Run Daily Batch** to trigger automated advisory generation.

2. **Sandbox Simulator (`/simulate`)**:
   - Select any coordinate in Maharashtra or click a preset (e.g. *Wheat CRI Irrigation Need (Pune)* or *Soybean High Wind Spray Hazard (Akola)*).
   - Click **Execute Simulation** to observe the live 5-step trace:
     - Step 1: Raw weather forecast & multi-depth soil moisture.
     - Step 2: Growth stage resolution from DAS.
     - Step 3: Deterministic rules engine output with reason codes and university citations.
     - Step 4: Vernacular natural-language SMS with character counter and Anti-Hallucination Guardrail verification verdict.
     - Step 5: Audio player streaming synthesized Google Cloud TTS audio in Hindi, Marathi, or English.

3. **Advisory Audit (`/advisories`)**:
   - View the side-by-side audit view comparing rules decisions, generated messages, and delivery logs.

4. **GKMS Evaluation (`/evaluation`)**:
   - Click **Run Evaluation Suite** to execute the benchmark against authentic IMD agromet bulletins and view the agreement matrix and discrepancy inspector.

---

## 9. Phase 2 Roadmap
- **Inbound IVR System**: Press 1 for today's advice; voice Q&A powered by Speech-to-Text grounded in Kisan Call Centre (KCC) queries.
- **Satellite Clients**: Integration of Sentinel-2 NDVI via Copernicus STAC API, CHIRPS rainfall, and NASA SMAP soil moisture.
- **WhatsApp Integration**: Meta WhatsApp Business API support for rich advisory cards with voice notes.
- **Mandi Price Hints**: Integration with Agmarknet (data.gov.in) for harvest marketing timing.

---

## License
Licensed under the Apache License 2.0. Offline datasets are subject to their respective government and institutional licenses documented in `/data/README.md`.
