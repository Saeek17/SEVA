# Comprehensive Repository Audit: KisanSaathi

**Audit Date:** October 28, 2026  
**Auditor:** Antigravity Engineering  
**Scope:** Honest Status Table & Verification (Checkpoint 1 — No production code written)

---

## 1. Twenty Features Honest Status Table

| # | Feature Requirement | Status | Evidence (File + Test Name) | Current Reality & Missing Pieces |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Registration by web form AND keyword ("START") on SMS/WhatsApp; STOP opt-out; consent capture** | **PARTIAL** | Web form: `FarmerRegistrationModal.tsx`<br>STOP test: `test_stop_opt_out_webhook` in `test_delivery.py` | Web registration and STOP webhook work. Inbound "START" keyword parser is **MISSING**; WhatsApp inbound keyword registration is **MISSING**. |
| **2** | **Daily morning advice: 2–3 short sentences, most urgent action first, one-line reason, <320 chars for SMS, spoken for voice** | **DONE** | File: `backend/app/services/advice_generator/generator.py`<br>Tests: `test_advice_generation_end_to_end_hindi` in `test_advice_generator.py`, `test_length_overflow_rejected` in `test_validator.py` | Rules + prompt builder generate structured advice constrained under 320 chars. |
| **3** | **Urgent alerts (heavy rain, heat stress, frost, long dry spell, strong wind), deduplicated for 24 hours** | **DONE** | Files: `rules_engine.py`, `deduplicator.py`<br>Tests: `test_alert_deduplication` in `test_delivery.py`, `test_spray_wind_drift_hazard` in `test_rules_engine.py` | Rules engine fires high-urgency alerts; `AlertDeduplicator` suppresses duplicate alert reason codes within a 24-hour window. |
| **4** | **Crop-stage awareness: advice changes automatically with days-after-sowing (DAS)** | **DONE** | Files: `stage_calculator.py`, `rules_engine.py`<br>Test: `test_critical_irrigation_trigger` in `test_rules_engine.py` | Computes phenological stage based on DAS and triggers stage-specific moisture/temperature/spray rules from crop YAML. |
| **5** | **Weekly outlook message (rain, temp trend, planning tip)** | **MISSING** | None (No file or test exists) | Completely absent. No aggregator or template exists for weekly outlook planning messages. |
| **6** | **Channel fallback cascade: WhatsApp fails -> SMS -> Voice call** | **MISSING** | None (No file or test exists) | Twilio SMS and Voice exist as isolated methods in `twilio_provider.py`. No WhatsApp dispatch, no delivery failure monitor, and no fallback cascade chain exist. |
| **7** | **Plain, jargon-free wording; simple numbers ("about 20 mm of rain")** | **DONE** | Files: `prompt_builder.py`, `validator.py`<br>Tests: `test_valid_irrigation_message_passes`, `test_hallucinated_number_rejected` in `test_validator.py` | Prompt templates enforce conversational tone and validator rejects unapproved numerical claims. |
| **8** | **Landing page: problem, pipeline, channels, languages, crops, data attribution** | **PARTIAL** | File: `frontend/src/app/page.tsx` | Informational sections exist inside the master dashboard, but they are tangled with admin controls instead of being an independent public landing page. |
| **9** | **Registration page with Leaflet map to pick field location** | **PARTIAL** | Files: `FarmerMap.tsx`, `FarmerRegistrationModal.tsx` | Map picker works, but soil type is currently a required manual dropdown instead of an automated SoilGrids lookup by coordinates with optional override. |
| **10** | **Simulate page: full pipeline live (raw data -> rules -> structured advice -> generated message -> audio) without sending real SMS** | **DONE** | Files: `backend/app/api/simulate.py`, `frontend/src/app/page.tsx`<br>Test: `test_simulate_farmer_pipeline` in `test_api_endpoints.py` | End-to-end sandbox pipeline works via `/api/v1/simulate` and UI simulator tab; needs its own dedicated clean public route `/simulate`. |
| **11** | **"Data & Methods" page: source details, resolution, update lag, limits** | **MISSING** | None (No dedicated page exists) | Only described in repository `README.md` and brief UI tooltips. No dedicated public `/methods` page exists. |
| **12** | **Login-protected farmer table (search/filter) and map** | **PARTIAL** | File: `frontend/src/app/page.tsx`<br>Test: `test_register_and_list_farmers` in `test_api_endpoints.py` | Farmer table and map markers render in the frontend, but there is **zero server-side or client-side authentication** protecting the routes or endpoints. |
| **13** | **Advice history: structured advice and generated message side by side, delivery status, sources used** | **DONE** | Files: `backend/app/api/advisories.py`, `frontend/src/app/page.tsx`<br>Test: `test_api_endpoints.py` | `/api/v1/advisories/history` returns structured items, message, delivery logs, and source list; displayed side-by-side in frontend Audit tab. |
| **14** | **Stats: sent/delivered/failed per channel, alerts by type, opt-outs, source failure rates** | **DONE** | Files: `backend/app/api/advisories.py`, `frontend/src/app/page.tsx`<br>Test: `test_api_endpoints.py` | `/api/v1/advisories/stats` computes channel breakdown, alert frequency, opt-out counts, and source failure counts; displayed on dashboard KPI cards. |
| **15** | **Crop config viewer with stages, thresholds, sources, and NEEDS_EXPERT_REVIEW badge** | **DONE** | Files: `backend/app/api/crops.py`, `frontend/src/app/page.tsx`<br>Tests: `test_get_all_crops`, `test_get_crop_detail_wheat` in `test_api_crops.py` | Displays crop parameters, university citations, and flags unverified values with yellow badges in the UI. |
| **16** | **Crops defined ONLY in `/config/crops/*.yaml`; no hardcoding; schema validator** | **DONE** | Files: `config/crops/wheat_maharashtra.yaml`, `soybean_maharashtra.yaml`, `loader.py`<br>Tests: `test_load_official_crops`, `test_malformed_overlapping_stages_fails_loudly` in `test_crop_schema.py` | Fully externalized in YAML. Schema validation rejects missing citations or overlapping stage definitions at startup. |
| **17** | **Deterministic rules engine (irrigation, spray, sowing, harvest, alerts) + LLM validation + DLT fallback** | **DONE** | Files: `rules_engine.py`, `validator.py`, `template_fallback.py`<br>Tests: `test_critical_irrigation_trigger`, `test_skip_irrigation_due_to_forecast_rain`, `test_spray_wind_drift_hazard` in `test_rules_engine.py`; `test_unapproved_spray_action_rejected` in `test_validator.py` | Complete deterministic decision engine. LLM output validated against rules; fallback templates used if validation fails. |
| **18** | **Evaluation harness against real IMD GKMS advisories** | **PARTIAL** | Files: `gkms_evaluator.py`<br>Test: `test_run_evaluation` in `test_evaluation.py` | Evaluator execution code works, but the benchmark file (`data/benchmarks/gkms_advisories.json`) contains only 6 synthetic/summarized cases without verifiable URLs. |
| **19** | **MOCK/dry-run mode via env flags (`DRY_RUN=true`, `MOCK_DATA=false`)** | **PARTIAL** | Files: `backend/app/config.py`, `twilio_provider.py`<br>Test: `test_twilio_mock_dispatch` in `test_delivery.py` | Backend switches to mock providers when credentials are blank. Missing visible frontend visual indicators/badges informing the user that mock mode is running. |
| **20** | **Phone numbers encrypted at rest (AES-256 Fernet), consent logged, STOP honored** | **DONE** | Files: `security.py`, `farmer.py`, `delivery_webhooks.py`<br>Tests: `test_stop_opt_out_webhook` in `test_delivery.py`, `test_register_and_list_farmers` in `test_api_endpoints.py` | Encrypted via Fernet in SQLite/PostgreSQL with deterministic HMAC-SHA256 indexing; STOP keyword opts out farmer. |

---

## 2. Explicit Feature Drilldown

1. **WhatsApp Delivery:** **MISSING.**  
   `TwilioDeliveryProvider` does not implement WhatsApp messaging. `TWILIO_WHATSAPP_NUMBER` is not utilized in dispatch.
2. **Voice Delivery:** **PARTIAL.**  
   `TwilioDeliveryProvider.make_voice_call` initiates TwiML outbound calls, but lacks DTMF interaction, call progress tracking, and busy/no-answer handling.
3. **Delivery-Status Webhooks and Retries:** **PARTIAL.**  
   Webhooks at `/api/v1/delivery/webhooks/sms` and `/webhooks/voice` record status changes in `DeliveryLog`. However, **automatic retry logic with exponential backoff is completely absent**.
4. **Channel Fallback (WhatsApp -> SMS -> Voice):** **MISSING.**  
   No sequential fallback logic exists. A failed message stops immediately with status `FAILED`.
5. **Weekly Outlook:** **MISSING.**  
   Only daily morning advisories and emergency hazard checks exist. No weekly planning advice pipeline is built.
6. **Keyword Registration ("START"):** **MISSING.**  
   Inbound webhook checks for `STOP`, `QUIT`, `थांबवा`, `रोकें`, but ignores inbound `START` or new registration via SMS/WhatsApp.
7. **STOP Opt-Out:** **DONE.**  
   `delivery_webhooks.py` sets `Farmer.is_active = False` on receiving `STOP` or regional equivalents. Verified by `test_stop_opt_out_webhook`.
8. **Admin Login:** **MISSING.**  
   JWT utility functions (`create_access_token`, `decode_access_token`) exist in `security.py`, but no login endpoint (`/auth/login`) exists and no backend API route requires authorization headers. The admin UI is completely unprotected.
9. **Data & Methods Page:** **MISSING.**  
   No public route exists documenting source resolution, update lag, scientific limitations, and CC BY 4.0 attribution.
10. **MOCK Labelling:** **PARTIAL.**  
    Dry-run mode is logged to standard output (`[DRY RUN SMS]`), but the frontend UI displays no indication that it is running in simulated/mock mode.

---

## 3. Direct Confirmation of Specific Checkpoint Items

### a. Real fixtures captured from live API calls?
* **Answer:** **NO.**
* **Evidence:** `backend/app/tests/fixtures/` is completely empty. `test_data_clients.py` uses a synthetic `DummyClient` and `force_mock=True` instead of asserting against real recorded HTTP payloads.
* **Why:** API responses were not recorded and committed to disk.
* **Command to run on your machine to capture fixtures:**  
  Run this one-line Python script from your project root to fetch Pune coordinates (18.5204, 73.8567) and save exact payloads:
  ```powershell
  python -c "import urllib.request, json, os; os.makedirs('backend/app/tests/fixtures', exist_ok=True); urllib.request.urlretrieve('https://api.open-meteo.com/v1/forecast?latitude=18.5204&longitude=73.8567&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,soil_temperature_0_to_7cm,soil_moisture_0_to_7cm&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Asia/Kolkata&forecast_days=7', 'backend/app/tests/fixtures/open_meteo.json'); print('Open-Meteo fixture saved'); urllib.request.urlretrieve('https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M_MAX,T2M_MIN&community=AG&longitude=73.8567&latitude=18.5204&start=20240501&end=20240530&format=JSON', 'backend/app/tests/fixtures/nasa_power.json'); print('NASA POWER fixture saved'); req = urllib.request.Request('https://rest.isric.org/soilgrids/v2.0/properties/query?lon=73.8567&lat=18.5204&property=clay&property=sand&property=silt&depth=0-5cm&depth=5-15cm&value=mean', headers={'User-Agent': 'KisanSaathi/1.0'}); open('backend/app/tests/fixtures/isric_soilgrids.json', 'wb').write(urllib.request.urlopen(req).read()); print('ISRIC SoilGrids fixture saved')"
  ```

### b. Scheduler moved out of the API into a standalone /worker?
* **Answer:** **NO.**
* **Evidence:** There is no `/worker` directory in the repository. The scheduler exists as `backend/app/services/scheduler/task_scheduler.py` inside the backend package.

### c. PostgreSQL is the only database for deployment (SQLite test-only)?
* **Answer:** **NO.**
* **Evidence:** `backend/app/config.py` line 19 defaults to `DATABASE_URL: str = "sqlite:///./kisansaathi.db"`. The application permits SQLite in all environments and does not enforce PostgreSQL when deployed.

### d. docs/ARCHITECTURE.md and docs/DEPLOYMENT.md exist and are accurate?
* **Answer:** **NO.**
* **Evidence:** `docs/` contains only `AUDIT.md`. Neither `docs/ARCHITECTURE.md` nor `docs/DEPLOYMENT.md` has been created.
