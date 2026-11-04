// One plain sentence explaining WHY the top advice was given, built from the numbers the rules engine
// actually used (AdviceItem.params). Returns null when those numbers are missing (e.g. a saved history entry).
type Lang = "mr" | "hi" | "en";
type Params = Record<string, unknown>;
type Line = { [L in Lang]: string };

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const fmt = (v: number) => String(Math.round(v * 10) / 10);

// Each entry lists the params it needs and builds the sentence in three languages.
const WHY: Record<string, { need: string[]; text: (p: Record<string, string>) => Line }> = {
  EXTREME_HEAT_STRESS: {
    need: ["temp_c", "threshold_c"],
    text: (p) => ({
      mr: `आज तापमान ${p.temp_c}°C पर्यंत जाईल, जे या अवस्थेसाठीच्या ${p.threshold_c}°C मर्यादेपेक्षा जास्त आहे.`,
      hi: `आज तापमान ${p.temp_c}°C तक जा सकता है, जो इस अवस्था की ${p.threshold_c}°C सीमा से ज़्यादा है।`,
      en: `It may reach ${p.temp_c}°C today, above the ${p.threshold_c}°C stress limit for this stage.`,
    }),
  },
  EXCESS_RAIN_WATERLOGGING: {
    need: ["rain_mm", "rain_48h_mm"],
    text: (p) => ({
      mr: `२४ तासांत सुमारे ${p.rain_mm} मिमी (४८ तासांत ${p.rain_48h_mm} मिमी) पाऊस अपेक्षित आहे; शेतात पाणी साचू शकते.`,
      hi: `24 घंटों में करीब ${p.rain_mm} मिमी (48 घंटों में ${p.rain_48h_mm} मिमी) बारिश का अनुमान है; खेत में पानी रुक सकता है।`,
      en: `About ${p.rain_mm} mm of rain is expected in 24 hours (${p.rain_48h_mm} mm in 48 hours); water may stand in the field.`,
    }),
  },
  COLD_FROST_INJURY_RISK: {
    need: ["min_temp_c", "threshold_c"],
    text: (p) => ({
      mr: `रात्री तापमान ${p.min_temp_c}°C पर्यंत घसरू शकते, जे ${p.threshold_c}°C च्या सुरक्षित मर्यादेखाली आहे.`,
      hi: `रात का तापमान ${p.min_temp_c}°C तक गिर सकता है, जो ${p.threshold_c}°C की सुरक्षित सीमा से कम है।`,
      en: `Night temperature may fall to ${p.min_temp_c}°C, below the ${p.threshold_c}°C safe limit.`,
    }),
  },
  PROLONGED_DRY_SPELL_DROUGHT: {
    need: ["dry_days", "soil_moisture_pct"],
    text: (p) => ({
      mr: `${p.dry_days} दिवस पाऊस झालेला नाही आणि जमिनीतील ओलावा फक्त ${p.soil_moisture_pct}% आहे.`,
      hi: `${p.dry_days} दिनों से बारिश नहीं हुई और मिट्टी की नमी सिर्फ ${p.soil_moisture_pct}% है।`,
      en: `No real rain for ${p.dry_days} days and soil moisture is only ${p.soil_moisture_pct}%.`,
    }),
  },
  MATURITY_WITHHOLD_IRRIGATION: {
    need: ["das"],
    text: (p) => ({
      mr: `पीक पक्व होण्याच्या जवळ आहे (${p.das} दिवस); दाणे नीट सुकण्यासाठी पाणी थांबवले जाते.`,
      hi: `फसल पकने के करीब है (${p.das} दिन); दाने ठीक से सूखें इसलिए पानी रोका जाता है।`,
      en: `The crop is close to maturity (${p.das} days old); water is withheld so the grain dries properly.`,
    }),
  },
  ANTICIPATED_RAIN_OR_SATURATED: {
    need: ["rain_mm", "soil_moisture_pct"],
    text: (p) => ({
      mr: `४८ तासांत ${p.rain_mm} मिमी पाऊस अपेक्षित आहे आणि जमिनीत ओलावा ${p.soil_moisture_pct}% आहे.`,
      hi: `48 घंटों में ${p.rain_mm} मिमी बारिश का अनुमान है और मिट्टी में नमी ${p.soil_moisture_pct}% है।`,
      en: `${p.rain_mm} mm of rain is expected in 48 hours and soil moisture is ${p.soil_moisture_pct}%.`,
    }),
  },
  CRITICAL_STAGE_MOISTURE_DEFICIT: {
    need: ["soil_moisture_pct", "trigger_pct"],
    text: (p) => ({
      mr: `जमिनीत ओलावा ${p.soil_moisture_pct}% आहे, या अवस्थेला लागणाऱ्या ${p.trigger_pct}% पेक्षा कमी.`,
      hi: `मिट्टी में नमी ${p.soil_moisture_pct}% है, जो इस अवस्था के लिए ज़रूरी ${p.trigger_pct}% से कम है।`,
      en: `Soil moisture is ${p.soil_moisture_pct}%, below the ${p.trigger_pct}% this crop stage needs.`,
    }),
  },
  SOIL_MOISTURE_DEPLETION: {
    need: ["soil_moisture_pct", "trigger_pct"],
    text: (p) => ({
      mr: `जमिनीत ओलावा ${p.soil_moisture_pct}% आहे, ${p.trigger_pct}% च्या मर्यादेखाली, आणि पावसाची शक्यता कमी आहे.`,
      hi: `मिट्टी में नमी ${p.soil_moisture_pct}% है, ${p.trigger_pct}% की सीमा से कम, और बारिश की संभावना कम है।`,
      en: `Soil moisture is ${p.soil_moisture_pct}%, below the ${p.trigger_pct}% trigger, and little rain is expected.`,
    }),
  },
  ADEQUATE_SOIL_MOISTURE: {
    need: ["soil_moisture_pct"],
    text: (p) => ({
      mr: `जमिनीत ओलावा ${p.soil_moisture_pct}% आहे, या अवस्थेसाठी पुरेसा; अतिरिक्त पाणी नको.`,
      hi: `मिट्टी में नमी ${p.soil_moisture_pct}% है, इस अवस्था के लिए काफ़ी; अतिरिक्त पानी नहीं चाहिए।`,
      en: `Soil moisture is ${p.soil_moisture_pct}%, enough for this stage, so no extra watering is needed.`,
    }),
  },
  PRE_HARVEST_INTERVAL_PROHIBITION: {
    need: ["das"],
    text: (p) => ({
      mr: `काढणीजवळ (${p.das} दिवस) फवारणी थांबवली जाते, म्हणजे धान्यावर औषधाचे अंश राहत नाहीत.`,
      hi: `कटाई के करीब (${p.das} दिन) छिड़काव रोका जाता है ताकि उपज पर दवा के अंश न रहें।`,
      en: `Spraying is stopped close to harvest (${p.das} days old) to avoid chemical residue.`,
    }),
  },
  HIGH_WIND_DRIFT_HAZARD: {
    need: ["wind_kmh", "max_safe_wind_kmh"],
    text: (p) => ({
      mr: `वाऱ्याचा वेग ${p.wind_kmh} किमी/तास आहे, फवारणीसाठीच्या ${p.max_safe_wind_kmh} किमी/तास मर्यादेपेक्षा जास्त; औषध वाहून जाईल.`,
      hi: `हवा की गति ${p.wind_kmh} किमी/घंटा है, छिड़काव की ${p.max_safe_wind_kmh} किमी/घंटा सीमा से ज़्यादा; दवा उड़ जाएगी।`,
      en: `Wind is ${p.wind_kmh} km/h, above the safe ${p.max_safe_wind_kmh} km/h for spraying; the spray would drift.`,
    }),
  },
  RAIN_WASHOFF_RISK: {
    need: ["rain_prob_pct", "forecast_rain_24h_mm"],
    text: (p) => ({
      mr: `पावसाची ${p.rain_prob_pct}% शक्यता (${p.forecast_rain_24h_mm} मिमी) असल्याने फवारलेले औषध धुऊन जाऊ शकते.`,
      hi: `बारिश की ${p.rain_prob_pct}% संभावना (${p.forecast_rain_24h_mm} मिमी) से छिड़की दवा धुल सकती है।`,
      en: `A ${p.rain_prob_pct}% chance of rain (${p.forecast_rain_24h_mm} mm) could wash the spray off.`,
    }),
  },
  HIGH_TEMP_EVAPORATION_SCORCH: {
    need: ["max_temp_c", "safe_temp_c"],
    text: (p) => ({
      mr: `तापमान ${p.max_temp_c}°C पर्यंत जाईल, फवारणीच्या ${p.safe_temp_c}°C मर्यादेपेक्षा जास्त; औषध उडून जाईल किंवा पाने करपतील.`,
      hi: `तापमान ${p.max_temp_c}°C तक जाएगा, छिड़काव की ${p.safe_temp_c}°C सीमा से ज़्यादा; दवा उड़ेगी या पत्ते झुलसेंगे।`,
      en: `It will reach ${p.max_temp_c}°C, above the ${p.safe_temp_c}°C safe limit for spraying; the spray would evaporate or scorch leaves.`,
    }),
  },
  FAVORABLE_SPRAY_WINDOW: {
    need: ["wind_kmh", "max_temp_c", "rain_prob_pct"],
    text: (p) => ({
      mr: `वारा ${p.wind_kmh} किमी/तास, तापमान ${p.max_temp_c}°C आणि पावसाची शक्यता फक्त ${p.rain_prob_pct}%: फवारणीसाठी चांगली वेळ.`,
      hi: `हवा ${p.wind_kmh} किमी/घंटा, तापमान ${p.max_temp_c}°C और बारिश की संभावना सिर्फ ${p.rain_prob_pct}%: छिड़काव के लिए अच्छा समय।`,
      en: `Wind ${p.wind_kmh} km/h, ${p.max_temp_c}°C and only a ${p.rain_prob_pct}% chance of rain: good conditions for spraying.`,
    }),
  },
  OPTIMAL_DRY_HARVEST_WINDOW: {
    need: ["forecast_rain_7d_mm"],
    text: (p) => ({
      mr: `पुढील ७ दिवसांत फक्त ${p.forecast_rain_7d_mm} मिमी पाऊस अपेक्षित आहे; काढणीसाठी कोरडा काळ.`,
      hi: `अगले 7 दिनों में सिर्फ ${p.forecast_rain_7d_mm} मिमी बारिश का अनुमान है; कटाई के लिए सूखा समय।`,
      en: `Only ${p.forecast_rain_7d_mm} mm of rain is expected in the next 7 days, a dry window for harvesting.`,
    }),
  },
};

export function whyText(reasonCode: string | undefined, params: Params | undefined, lang: Lang): string | null {
  const rule = reasonCode ? WHY[reasonCode] : undefined;
  if (!rule || !params) return null;
  const values: Record<string, string> = {};
  for (const key of rule.need) {
    const n = num(params[key]);
    if (n === null) return null;
    values[key] = fmt(n);
  }
  return rule.text(values)[lang];
}
