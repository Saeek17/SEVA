# KisanSaathi Offline Reference & Evaluation Data

This directory houses offline benchmark datasets, language lexicons, few-shot prompt corpora, and Kisan Call Centre (KCC) query logs used for system validation, DLT template fallback, and natural language generation.

## Inventory of Data Files

| Directory / File | Description | Source & Attribution | License | Usage in KisanSaathi |
|---|---|---|---|---|
| `benchmarks/gkms_advisories.json` | Authentic district agromet bulletins issued by IMD Gramin Krishi Mausam Sewa (GKMS) | IMD GKMS Pune / State Agromet Advisory Bulletins (imdpune.gov.in / agromet.imd.gov.in) | Open Access / Gov of India (GODL-India) | Ground-truth benchmark for evaluating rules engine accuracy; few-shot examples in LLM prompts |
| `kcc_samples/sample_queries.json` | Anonymized farmer questions from Kisan Call Centre query logs | Ministry of Agriculture & Farmers Welfare, Government of India (data.gov.in) | Government Open Data License - India (GODL-India) | Linguistic intent validation, query understanding for Phase 2 voice Q&A |
| `language/dlt_templates.json` | Pre-certified, DLT-registered SMS/Voice templates in Hindi, Marathi, English | Telecom Commercial Communications Customer Preference Regulations (TCCCPR, 2018) / TRAI | Proprietary / System certified | Deterministic fallback when LLM output fails anti-hallucination guardrail validation |
| `language/agricultural_glossary.json` | Verified vernacular agricultural terminology | AI4Bharat (IIT Madras) & Digital India Bhashini Glossary | CC-BY-4.0 / Bhashini Open Resource | Vocabulary alignment for Gemini prompts and guardrail verb/noun checks |

## Attribution & Terms of Use
- **IMD GKMS**: "Data supplied courtesy of India Meteorological Department (IMD), Ministry of Earth Sciences, Government of India."
- **Data.gov.in**: "National Data Sharing and Accessibility Policy (NDSAP), Government of India."
- **AI4Bharat**: "AI4Bharat, Indian Institute of Technology Madras, under Digital India Initiative."
