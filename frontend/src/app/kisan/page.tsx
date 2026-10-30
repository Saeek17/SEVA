"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { CropMetadata, SimulationResult, AdviceItem } from "@/lib/types";
import { DailyAlerts } from "@/components/kisan/DailyAlerts";
import { VoiceInput } from "@/components/kisan/VoiceInput";
import type { ParsedSpeech } from "@/lib/voiceParse";

type Lang = "mr" | "hi" | "en";

const API_ORIGIN = (() => {
  try {
    return new URL(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").origin;
  } catch {
    return "http://localhost:8000";
  }
})();

const T = {
  title: { mr: "किसान साथी", hi: "किसान साथी", en: "Kisan Saathi" },
  sub: {
    mr: "तुमच्या शेतासाठी आजचा सल्ला",
    hi: "आपके खेत के लिए आज की सलाह",
    en: "Today's advice for your farm",
  },
  q1: { mr: "१. तुमचे पीक कोणते?", hi: "१. आपकी फसल कौन सी है?", en: "1. Which crop?" },
  q2: { mr: "२. तुमचा जिल्हा?", hi: "२. आपका जिला?", en: "2. Your district?" },
  q3: { mr: "३. पीक किती दिवसांचे?", hi: "३. फसल कितने दिन की है?", en: "3. How old is the crop?" },
  gps: { mr: "📍 माझे ठिकाण वापरा", hi: "📍 मेरी लोकेशन इस्तेमाल करें", en: "📍 Use my location" },
  gpsOk: { mr: "✔ तुमचे ठिकाण मिळाले", hi: "✔ आपकी लोकेशन मिल गई", en: "✔ Location found" },
  gpsFail: {
    mr: "ठिकाण मिळाले नाही. कृपया यादीतून तुमचा जिल्हा निवडा.",
    hi: "लोकेशन नहीं मिली। कृपया सूची से अपना जिला चुनें।",
    en: "Couldn't get your location. Please pick your district from the list.",
  },
  go: { mr: "आजचा सल्ला पहा", hi: "आज की सलाह देखें", en: "Show today's advice" },
  loading: { mr: "सल्ला तयार होत आहे…", hi: "सलाह तैयार हो रही है…", en: "Preparing advice…" },
  listen: { mr: "🔊 ऐका", hi: "🔊 सुनें", en: "🔊 Listen" },
  stop: { mr: "⏹ थांबवा", hi: "⏹ रोकें", en: "⏹ Stop" },
  change: { mr: "✏️ माहिती बदला", hi: "✏️ जानकारी बदलें", en: "✏️ Change details" },
  refresh: { mr: "🔄 पुन्हा तपासा", hi: "🔄 फिर से जांचें", en: "🔄 Check again" },
  more: { mr: "इतर सूचना", hi: "अन्य सूचनाएं", en: "Other notes" },
  error: {
    mr: "सल्ला मिळवता आला नाही. इंटरनेट तपासा आणि पुन्हा प्रयत्न करा.",
    hi: "सलाह नहीं मिल सकी। इंटरनेट जांचें और फिर कोशिश करें।",
    en: "Could not get advice. Check your internet and try again.",
  },
  needAll: {
    mr: "कृपया पीक, जिल्हा आणि पिकाचे वय निवडा.",
    hi: "कृपया फसल, जिला और फसल की उम्र चुनें।",
    en: "Please choose crop, district and crop age.",
  },
  sms: {
    mr: "इंटरनेट नाही? सल्ला SMS वर मिळवण्यासाठी तुमच्या कृषी केंद्राशी संपर्क करा.",
    hi: "इंटरनेट नहीं है? SMS पर सलाह पाने के लिए अपने कृषि केंद्र से संपर्क करें।",
    en: "No internet? Ask your agriculture centre to get this advice by SMS.",
  },
} as const;

const PLACES = [
  { id: "nashik", lat: 20.0063, lon: 73.8077, n: { mr: "नाशिक", hi: "नाशिक", en: "Nashik" } },
  { id: "pune", alt: ["पुण्य"], lat: 18.5204, lon: 73.8567, n: { mr: "पुणे", hi: "पुणे", en: "Pune" } },
  { id: "nagpur", lat: 21.1458, lon: 79.0882, n: { mr: "नागपूर", hi: "नागपुर", en: "Nagpur" } },
  { id: "latur", lat: 18.4088, lon: 76.5604, n: { mr: "लातूर", hi: "लातूर", en: "Latur" } },
  { id: "ahmednagar", lat: 19.0948, lon: 74.748, n: { mr: "अहमदनगर", hi: "अहमदनगर", en: "Ahmednagar" } },
  { id: "akola", alt: ["अकोल"], lat: 20.7002, lon: 77.0082, n: { mr: "अकोला", hi: "अकोला", en: "Akola" } },
  { id: "kolhapur", lat: 16.705, lon: 74.2433, n: { mr: "कोल्हापूर", hi: "कोल्हापुर", en: "Kolhapur" } },
  { id: "sambhajinagar", lat: 19.8762, lon: 75.3433, n: { mr: "छत्रपती संभाजीनगर", hi: "छत्रपति संभाजीनगर", en: "Chh. Sambhajinagar" } },
  { id: "solapur", lat: 17.6599, lon: 75.9064, n: { mr: "सोलापूर", hi: "सोलापुर", en: "Solapur" } },
  { id: "jalgaon", lat: 21.0077, lon: 75.5626, n: { mr: "जळगाव", hi: "जलगांव", en: "Jalgaon" } },
  { id: "satara", alt: ["साता"], lat: 17.6805, lon: 74.0183, n: { mr: "सातारा", hi: "सतारा", en: "Satara" } },
  { id: "yavatmal", lat: 20.3899, lon: 78.1307, n: { mr: "यवतमाळ", hi: "यवतमाल", en: "Yavatmal" } },
];

// Farmers rarely know an exact sowing date, so ask for a rough age.
const AGES = [
  { id: "new", das: 20, n: { mr: "नुकतीच पेरणी (१ महिन्याच्या आत)", hi: "अभी बोई है (1 महीने के अंदर)", en: "Just sown (under 1 month)" } },
  { id: "m2", das: 45, n: { mr: "१ ते २ महिने", hi: "1 से 2 महीने", en: "1 to 2 months" } },
  { id: "m3", das: 75, n: { mr: "२ ते ३ महिने", hi: "2 से 3 महीने", en: "2 to 3 months" } },
  { id: "old", das: 105, n: { mr: "३ महिन्यांपेक्षा जास्त", hi: "3 महीने से ज्यादा", en: "More than 3 months" } },
  { id: "ready", das: -1, n: { mr: "कापणीला तयार", hi: "कटाई के लिए तैयार", en: "Ready to harvest" } },
];

const CROP_EMOJI: Record<string, string> = {
  rice: "🌾", wheat: "🌿", cotton: "☁️", maize: "🌽", tomato: "🍅", sugarcane: "🎋", soybean: "🫘",
};

const ACTIONS: Record<string, { icon: string; tone: "good" | "warn" | "bad"; n: Record<Lang, string> }> = {
  IRRIGATE: { icon: "💧", tone: "warn", n: { mr: "आज पाणी द्या", hi: "आज पानी दें", en: "Irrigate today" } },
  SCHEDULE_IRRIGATION: { icon: "💧", tone: "warn", n: { mr: "पाणी देण्याची तयारी करा", hi: "सिंचाई की तैयारी करें", en: "Plan irrigation" } },
  SKIP_IRRIGATION: { icon: "🚫", tone: "good", n: { mr: "आज पाणी देऊ नका", hi: "आज सिंचाई न करें", en: "No irrigation today" } },
  SAFE_SPRAY: { icon: "✅", tone: "good", n: { mr: "आज फवारणी करू शकता", hi: "आज छिड़काव कर सकते हैं", en: "Safe to spray today" } },
  AVOID_SPRAY: { icon: "⚠️", tone: "warn", n: { mr: "आज फवारणी करू नका", hi: "आज छिड़काव न करें", en: "Do not spray today" } },
  HEAT_ALERT: { icon: "🔥", tone: "bad", n: { mr: "उष्णतेचा इशारा", hi: "गर्मी की चेतावनी", en: "Heat warning" } },
  FROST_ALERT: { icon: "❄️", tone: "bad", n: { mr: "थंडीचा इशारा", hi: "पाले की चेतावनी", en: "Frost warning" } },
  RAIN_ALERT: { icon: "🌧️", tone: "bad", n: { mr: "जोरदार पावसाचा इशारा", hi: "भारी बारिश की चेतावनी", en: "Heavy rain warning" } },
  DROUGHT_ALERT: { icon: "🏜️", tone: "bad", n: { mr: "कोरड्या हवामानाचा इशारा", hi: "सूखे की चेतावनी", en: "Dry spell warning" } },
  HARVEST_READY: { icon: "🌾", tone: "good", n: { mr: "कापणीची वेळ झाली", hi: "कटाई का समय हुआ", en: "Time to harvest" } },
  MONITOR_CROP: { icon: "👀", tone: "good", n: { mr: "पिकावर लक्ष ठेवा", hi: "फसल पर नज़र रखें", en: "Keep watching the crop" } },
};

const TONE = {
  good: "bg-emerald-50 border-emerald-300 text-emerald-900",
  warn: "bg-amber-50 border-amber-300 text-amber-900",
  bad: "bg-red-50 border-red-300 text-red-900",
};

interface Profile {
  lang: Lang;
  cropId: string;
  placeId: string;
  gps?: { lat: number; lon: number };
  ageId: string;
}

const STORE_KEY = "kisan_profile_v1";

function cropEmoji(cropId: string) {
  const key = Object.keys(CROP_EMOJI).find((k) => cropId.startsWith(k));
  return key ? CROP_EMOJI[key] : "🌱";
}

function readProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? (JSON.parse(raw) as Profile) : null;
  } catch {
    return null;
  }
}

export default function KisanPage() {
  const [lang, setLang] = useState<Lang>("mr");
  const [crops, setCrops] = useState<CropMetadata[]>([]);
  const [cropId, setCropId] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [gps, setGps] = useState<{ lat: number; lon: number } | undefined>();
  const [ageId, setAgeId] = useState("");
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const t = (k: keyof typeof T) => T[k][lang];

  const loadAdvice = async (p: Profile, cropList: CropMetadata[]) => {
    const crop = cropList.find((c) => c.crop_id === p.cropId);
    const place = PLACES.find((x) => x.id === p.placeId);
    const age = AGES.find((a) => a.id === p.ageId);
    const coords = p.gps || (place && { lat: place.lat, lon: place.lon });
    if (!crop || !age || !coords) return;

    const das = age.das === -1 ? Math.max(1, crop.typical_duration_days - 3) : age.das;
    setLoading(true);
    setError("");
    try {
      const res = await api.simulateFarmer({
        latitude: coords.lat,
        longitude: coords.lon,
        crop_id: crop.crop_id,
        das,
        language: p.lang,
      });
      setResult(res);
    } catch {
      setError(T.error[p.lang]);
    } finally {
      setLoading(false);
    }
  };

  // First load: crops from the backend, then jump straight to advice for a returning farmer.
  useEffect(() => {
    const saved = readProfile();
    if (saved) {
      setLang(saved.lang);
      setCropId(saved.cropId);
      setPlaceId(saved.placeId);
      setGps(saved.gps);
      setAgeId(saved.ageId);
    }
    api
      .getCrops()
      .then((list) => {
        setCrops(list);
        if (saved) loadAdvice(saved, list);
      })
      .catch(() => setError(T.error[saved?.lang || "mr"]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch in the new language when the farmer switches language on the result screen.
  const switchLang = (l: Lang) => {
    setLang(l);
    stopAudio();
    if (result && cropId && ageId) {
      const p: Profile = { lang: l, cropId, placeId, gps, ageId };
      try {
        localStorage.setItem(STORE_KEY, JSON.stringify(p));
      } catch {}
      loadAdvice(p, crops);
    }
  };

  const submit = () => {
    if (!cropId || !ageId || !(placeId || gps)) {
      setError(t("needAll"));
      return;
    }
    const p: Profile = { lang, cropId, placeId, gps, ageId };
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(p));
    } catch {}
    loadAdvice(p, crops);
  };

  const useGps = () => {
    // Browsers only expose geolocation on HTTPS (or localhost); fail with a clear hint otherwise.
    if (!navigator.geolocation || !window.isSecureContext) {
      setError(t("gpsFail"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setError("");
        setGps({ lat: pos.coords.latitude, lon: pos.coords.longitude });
        setPlaceId("");
      },
      () => setError(t("gpsFail")),
      { timeout: 10000, maximumAge: 300000 }
    );
  };

  const stopAudio = () => {
    audioRef.current?.pause();
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    setPlaying(false);
  };

  const speakFallback = (text: string) => {
    if (!("speechSynthesis" in window)) return;
    const clean = text.replace(/^(किसान साथी|KisanSaathi):/, "").trim();
    const u = new SpeechSynthesisUtterance(clean);
    const voices = window.speechSynthesis.getVoices();
    const want = lang === "en" ? "en-in" : "hi";
    const v = voices.find((x) => x.lang.toLowerCase().replace("_", "-").startsWith(want));
    if (v) {
      u.voice = v;
      u.lang = v.lang;
    }
    u.onend = () => setPlaying(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    setPlaying(true);
  };

  const toggleListen = () => {
    if (playing) return stopAudio();
    if (!result) return;
    const url = result.voice_audio_url?.startsWith("http")
      ? result.voice_audio_url
      : result.voice_audio_url
      ? `${API_ORIGIN}${result.voice_audio_url}`
      : "";
    const audio = audioRef.current;
    if (audio && url) {
      audio.src = url;
      audio.onended = () => setPlaying(false);
      audio.play().then(() => setPlaying(true)).catch(() => speakFallback(result.generated_message));
    } else {
      speakFallback(result.generated_message);
    }
  };

  const editDetails = () => {
    stopAudio();
    setResult(null);
    setError("");
  };

  const cropName = (c: CropMetadata) =>
    lang === "mr" ? c.common_name_mr : lang === "hi" ? c.common_name_hi : c.common_name_en;

  const applySpoken = (p: ParsedSpeech) => {
    if (p.cropId) setCropId(p.cropId);
    if (p.placeId) {
      setPlaceId(p.placeId);
      setGps(undefined);
    }
    if (p.ageId) setAgeId(p.ageId);
    setError("");
  };

  const voiceCrops = crops.map((c) => ({
    id: c.crop_id,
    names: [c.common_name_mr, c.common_name_hi, c.common_name_en, c.crop_id.split("_")[0]],
  }));
  const voicePlaces = PLACES.map((p) => ({ id: p.id, names: [p.n.mr, p.n.hi, p.n.en, ...(p.alt || [])] }));
  const voiceAges = AGES.map((a) => ({ id: a.id, das: a.das }));

  const alertPlace = PLACES.find((x) => x.id === placeId);
  const alertCoords = gps || (alertPlace && { lat: alertPlace.lat, lon: alertPlace.lon });

  const headline: AdviceItem | undefined = result?.advice_items?.[0];
  const hero = headline ? ACTIONS[headline.action] || ACTIONS.MONITOR_CROP : null;
  const others = (result?.advice_items || []).slice(1);

  return (
    <div className="min-h-screen bg-[#f3f8f4] text-slate-900">
      <audio ref={audioRef} preload="none" />

      {/* Header */}
      <header className="bg-[#0b3d2a] text-white px-4 pt-5 pb-4">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-extrabold leading-tight">🌱 {t("title")}</h1>
              <p className="text-sm text-emerald-100/90 mt-0.5">{t("sub")}</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2" role="group" aria-label="Language">
            {(["mr", "hi", "en"] as Lang[]).map((l) => (
              <button
                key={l}
                onClick={() => switchLang(l)}
                className={`h-12 rounded-xl text-base font-bold border-2 transition active:scale-95 ${
                  lang === l
                    ? "bg-white text-[#0b3d2a] border-white"
                    : "bg-transparent text-white border-emerald-300/50"
                }`}
              >
                {l === "mr" ? "मराठी" : l === "hi" ? "हिंदी" : "English"}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-5 pb-16">
        {loading && (
          <div className="py-16 text-center">
            <div className="mx-auto h-12 w-12 rounded-full border-4 border-emerald-200 border-t-emerald-600 animate-spin" />
            <p className="mt-4 text-lg font-semibold text-emerald-900">{t("loading")}</p>
          </div>
        )}

        {/* RESULT */}
        {!loading && result && hero && headline && (
          <div className="space-y-4">
            <div className={`rounded-3xl border-2 p-5 ${TONE[hero.tone]}`}>
              <div className="text-6xl leading-none">{hero.icon}</div>
              <h2 className="mt-3 text-3xl font-extrabold leading-snug">{hero.n[lang]}</h2>
              <p className="mt-3 text-xl leading-relaxed">
                {result.generated_message.replace(/^(किसान साथी|KisanSaathi):\s*/, "")}
              </p>
            </div>

            <button
              onClick={toggleListen}
              className="w-full h-16 rounded-2xl bg-emerald-600 text-white text-2xl font-extrabold shadow-lg active:scale-[0.98] transition"
            >
              {playing ? t("stop") : t("listen")}
            </button>

            {others.length > 0 && (
              <section>
                <h3 className="text-base font-bold text-slate-600 mb-2">{t("more")}</h3>
                <ul className="space-y-2">
                  {others.map((it, i) => {
                    const a = ACTIONS[it.action] || ACTIONS.MONITOR_CROP;
                    return (
                      <li
                        key={i}
                        className={`flex items-center gap-3 rounded-2xl border-2 px-4 py-3 text-lg font-semibold ${TONE[a.tone]}`}
                      >
                        <span className="text-3xl">{a.icon}</span>
                        <span>{a.n[lang]}</span>
                      </li>
                    );
                  })}
                </ul>
              </section>
            )}

            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                onClick={() => {
                  const p = readProfile();
                  if (p) loadAdvice({ ...p, lang }, crops);
                }}
                className="h-14 rounded-2xl bg-white border-2 border-emerald-300 text-emerald-900 text-base font-bold active:scale-95"
              >
                {t("refresh")}
              </button>
              <button
                onClick={editDetails}
                className="h-14 rounded-2xl bg-white border-2 border-slate-300 text-slate-800 text-base font-bold active:scale-95"
              >
                {t("change")}
              </button>
            </div>

            {alertCoords && (
              <DailyAlerts
                ctx={{
                  lang,
                  cropId: result.crop_id,
                  das: result.das,
                  latitude: alertCoords.lat,
                  longitude: alertCoords.lon,
                  district: alertPlace?.n.en,
                }}
              />
            )}

            <p className="text-sm text-slate-500 text-center pt-2">{t("sms")}</p>
          </div>
        )}

        {/* SETUP FORM */}
        {!loading && !result && (
          <div className="space-y-7">
            {error && (
              <div className="rounded-2xl bg-red-50 border-2 border-red-300 text-red-900 p-4 text-lg font-semibold">
                {error}
              </div>
            )}

            <VoiceInput
              lang={lang}
              crops={voiceCrops}
              places={voicePlaces}
              ages={voiceAges}
              current={{ cropId, placeHasValue: !!(placeId || gps), ageId }}
              onParsed={applySpoken}
            />

            <section>
              <h2 className="text-xl font-extrabold mb-3">{t("q1")}</h2>
              <div className="grid grid-cols-2 gap-3">
                {crops.map((c) => (
                  <button
                    key={c.crop_id}
                    onClick={() => setCropId(c.crop_id)}
                    className={`rounded-2xl border-2 py-4 px-2 text-center active:scale-95 transition ${
                      cropId === c.crop_id
                        ? "bg-emerald-600 text-white border-emerald-700 shadow-md"
                        : "bg-white border-slate-300"
                    }`}
                  >
                    <div className="text-4xl">{cropEmoji(c.crop_id)}</div>
                    <div className="mt-1 text-lg font-bold">{cropName(c)}</div>
                  </button>
                ))}
              </div>
            </section>

            <section>
              <h2 className="text-xl font-extrabold mb-3">{t("q2")}</h2>
              <select
                value={placeId}
                onChange={(e) => {
                  setPlaceId(e.target.value);
                  setGps(undefined);
                }}
                className="w-full h-14 rounded-2xl border-2 border-slate-300 bg-white px-4 text-lg font-semibold"
              >
                <option value="">— {t("q2")} —</option>
                {PLACES.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.n[lang]}
                  </option>
                ))}
              </select>
              <button
                onClick={useGps}
                className="mt-3 w-full h-14 rounded-2xl bg-white border-2 border-emerald-300 text-emerald-900 text-lg font-bold active:scale-95"
              >
                {gps ? t("gpsOk") : t("gps")}
              </button>
            </section>

            <section>
              <h2 className="text-xl font-extrabold mb-3">{t("q3")}</h2>
              <div className="space-y-3">
                {AGES.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => setAgeId(a.id)}
                    className={`w-full h-14 rounded-2xl border-2 text-lg font-bold px-4 text-left active:scale-[0.98] transition ${
                      ageId === a.id
                        ? "bg-emerald-600 text-white border-emerald-700 shadow-md"
                        : "bg-white border-slate-300"
                    }`}
                  >
                    {a.n[lang]}
                  </button>
                ))}
              </div>
            </section>

            <button
              onClick={submit}
              className="w-full h-16 rounded-2xl bg-[#0b3d2a] text-white text-2xl font-extrabold shadow-lg active:scale-[0.98] transition"
            >
              {t("go")} ➜
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
