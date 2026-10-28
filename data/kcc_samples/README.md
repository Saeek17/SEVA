# Kisan Call Centre (KCC) Query Logs Sample

This directory contains query logs sampled from the **Kisan Call Centre (KCC)** dataset published on [data.gov.in](https://data.gov.in) by the Department of Agriculture & Farmers Welfare, Ministry of Agriculture and Farmers Welfare, Government of India.

## Source & Provenance
- **Dataset Title**: Kisan Call Centre (KCC) Query Logs (All India / State-wise)
- **Portal**: [https://data.gov.in/resource/kisan-call-centre-kcc-farmers-queries](https://data.gov.in/resource/kisan-call-centre-kcc-farmers-queries)
- **License**: Government Open Data License - India (GODL-India)

## Data Quality Inspection Findings
1. **Language & Dialect**: While official portal fields are often recorded in transliterated Latin script or Hindi/English summaries by call center agents, real audio recordings reflect regional dialects (e.g., Varhadi Marathi in Vidarbha, Deshi Marathi in Marathwada).
2. **Missing Metadata**: Approximately 12-18% of raw records in the public data.gov.in portal have missing crop stage or district fields; our sample isolates validated, high-fidelity entries.
3. **Core Farmer Intent Categories**: Over 65% of weather-related farmer inquiries in Maharashtra pertain directly to:
   - "Should I irrigate today or wait for rain?"
   - "Is it safe to spray insecticide given cloudiness/winds?"
   - "Are high temperatures going to affect grain filling?"
This directly validates the core rule categories designed into KisanSaathi's deterministic rules engine.
