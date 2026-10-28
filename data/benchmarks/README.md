# GKMS Advisory Evaluation Benchmarks

This directory stores ground-truth district agromet advisories issued by the **Gramin Krishi Mausam Sewa (GKMS)**, a joint initiative of the **India Meteorological Department (IMD)**, State Agricultural Universities (SAUs), and ICAR.

## Official Data Sources
- **IMD Agromet Advisory Service Portal**: [https://agromet.imd.gov.in](https://agromet.imd.gov.in)
- **IMD Pune Agromet Division**: [https://imdpune.gov.in](https://imdpune.gov.in)
- **MPKV Rahuri Agromet Bulletins**: [https://mpkv.ac.in](https://mpkv.ac.in)
- **VNMKV Parbhani Agromet Bulletins**: [https://vnmkv.ac.in](https://vnmkv.ac.in)

## Benchmark Schema Format
Each entry in `gkms_advisories.json` contains:
```json
{
  "id": "Unique identifier (e.g. GKMS-MH-PUN-2023-11-24)",
  "district": "District name in Maharashtra",
  "state": "Maharashtra",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "bulletin_date": "YYYY-MM-DD",
  "crop_id": "Matching crop_id in /config/crops",
  "growth_stage": "Stage name from bulletin",
  "das": 21,
  "source_bulletin": "Official bulletin document number and date",
  "observed_conditions": {
    "forecast_rain_48h_mm": 0.0,
    "max_temp_c": 29.5,
    "min_temp_c": 14.2,
    "wind_speed_kmh": 8.0,
    "soil_moisture_pct": 28.0
  },
  "expert_advice": {
    "irrigation": "IRRIGATE | SKIP_IRRIGATION",
    "spray": "SAFE_SPRAY | AVOID_SPRAY",
    "alert": "HEAT_ALERT | RAIN_ALERT | NONE",
    "expert_summary_en": "Verbatim recommendation from expert advisory"
  }
}
```

## Adding New Benchmark Records
1. Download official bi-weekly GKMS agromet bulletin PDFs (issued Tuesdays and Fridays) from IMD Pune or SAU websites.
2. Extract the crop, growth stage, observed and forecast weather, and official recommendations for irrigation and crop protection.
3. Append the record to `gkms_advisories.json` citing the exact bulletin number and date.
4. **Never fabricate benchmark records**: If a district or crop is not yet present, run the evaluation on available ground truth records.
