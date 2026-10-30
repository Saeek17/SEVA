"use client";

import { useEffect, useRef, useState } from "react";
import { parseSpoken, ParsedSpeech, ParseAge, ParseCrop, ParsePlace } from "@/lib/voiceParse";

type Lang = "mr" | "hi" | "en";

const T = {
  speak: { mr: "🎤 बोलून सांगा", hi: "🎤 बोलकर बताएं", en: "🎤 Speak instead" },
  hint: {
    mr: "उदा. “तूर, लातूर, ४५ दिवस”",
    hi: "जैसे “तूर, लातूर, 45 दिन”",
    en: "e.g. “tur, Latur, 45 days”",
  },
  listening: { mr: "ऐकत आहे… बोला", hi: "सुन रहा है… बोलिए", en: "Listening… speak now" },
  heard: { mr: "ऐकले:", hi: "सुना:", en: "Heard:" },
  nothing: {
    mr: "समजले नाही. पीक, जिल्हा आणि वय पुन्हा सांगा.",
    hi: "समझ नहीं आया। फसल, जिला और उम्र फिर बताएं।",
    en: "Couldn't understand. Please say crop, district and age again.",
  },
  missing: { mr: "अजून हवे:", hi: "अभी चाहिए:", en: "Still needed:" },
  allSet: { mr: "✔ सर्व माहिती मिळाली. खाली 'आजचा सल्ला पहा' दाबा.", hi: "✔ सारी जानकारी मिल गई। नीचे 'आज की सलाह देखें' दबाएं।", en: "✔ Got everything. Tap 'Show today's advice' below." },
  crop: { mr: "पीक", hi: "फसल", en: "crop" },
  place: { mr: "जिल्हा", hi: "जिला", en: "district" },
  age: { mr: "वय", hi: "उम्र", en: "age" },
  fail: {
    mr: "माईक चालू झाला नाही. सेटिंग्जमध्ये मायक्रोफोन व डिक्टेशन परवानगी तपासा.",
    hi: "माइक चालू नहीं हुआ। सेटिंग में माइक्रोफोन और डिक्टेशन की अनुमति जांचें।",
    en: "Couldn't start the microphone. Check microphone and dictation permissions.",
  },
} as const;

const RECOGNITION_LANG: Record<Lang, string> = { mr: "mr-IN", hi: "hi-IN", en: "en-IN" };

// Browser speech recognition is vendor-prefixed and has no bundled TypeScript types.
type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((e: any) => void) | null;
  onerror: ((e: any) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function getRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

interface Props {
  lang: Lang;
  crops: ParseCrop[];
  places: ParsePlace[];
  ages: ParseAge[];
  current: { cropId: string; placeHasValue: boolean; ageId: string };
  onParsed: (parsed: ParsedSpeech) => void;
}

export function VoiceInput({ lang, crops, places, ages, current, onParsed }: Props) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [heard, setHeard] = useState("");
  const [status, setStatus] = useState<"idle" | "ok" | "nothing" | "fail">("idle");
  const [missing, setMissing] = useState<string[]>([]);
  const recRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => setSupported(!!getRecognitionCtor()), []);
  useEffect(() => () => recRef.current?.stop(), []);

  if (!supported) return null;

  const start = (recLang: string, retried = false) => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) return;
    const rec = new Ctor();
    recRef.current = rec;
    rec.lang = recLang;
    rec.interimResults = false;
    rec.maxAlternatives = 3;

    let gotResult = false;
    rec.onresult = (e: any) => {
      gotResult = true;
      // Try every alternative the recogniser offers and keep the one that understands the most.
      const alts: string[] = [];
      for (let i = 0; i < e.results[0].length; i++) alts.push(e.results[0][i].transcript);
      let best: ParsedSpeech = {};
      let bestScore = -1;
      let bestText = alts[0] || "";
      for (const text of alts) {
        const parsed = parseSpoken(text, { crops, places, ages });
        const score = [parsed.cropId, parsed.placeId, parsed.ageId].filter(Boolean).length;
        if (score > bestScore) [best, bestScore, bestText] = [parsed, score, text];
      }
      setHeard(bestText);
      if (bestScore === 0) {
        setStatus("nothing");
        setMissing([]);
        return;
      }
      onParsed(best);
      const stillMissing = [
        !(best.cropId || current.cropId) && T.crop[lang],
        !(best.placeId || current.placeHasValue) && T.place[lang],
        !(best.ageId || current.ageId) && T.age[lang],
      ].filter(Boolean) as string[];
      setMissing(stillMissing);
      setStatus("ok");
    };
    rec.onerror = (e: any) => {
      // Some devices have no Marathi recogniser; fall back to Hindi, which understands the same crop/district names.
      if (e.error === "language-not-supported" && !retried && recLang !== "hi-IN") {
        start("hi-IN", true);
        return;
      }
      if (e.error !== "no-speech" && e.error !== "aborted") setStatus("fail");
    };
    rec.onend = () => {
      setListening(false);
      if (!gotResult) setStatus((s) => (s === "fail" ? s : "nothing"));
    };

    try {
      setHeard("");
      setStatus("idle");
      rec.start();
      setListening(true);
    } catch {
      setStatus("fail");
      setListening(false);
    }
  };

  const toggle = () => {
    if (listening) return recRef.current?.stop();
    start(RECOGNITION_LANG[lang]);
  };

  return (
    <section className="rounded-3xl bg-white border-2 border-emerald-300 p-4">
      <button
        onClick={toggle}
        className={`w-full h-16 rounded-2xl text-xl font-extrabold active:scale-[0.98] transition ${
          listening ? "bg-red-600 text-white animate-pulse" : "bg-emerald-700 text-white"
        }`}
      >
        {listening ? T.listening[lang] : T.speak[lang]}
      </button>
      <p className="mt-2 text-center text-sm text-slate-500">{T.hint[lang]}</p>
      {heard && (
        <p className="mt-3 text-lg">
          <span className="font-bold">{T.heard[lang]}</span> “{heard}”
        </p>
      )}
      {status === "nothing" && <p className="mt-2 text-base font-semibold text-red-700">{T.nothing[lang]}</p>}
      {status === "fail" && <p className="mt-2 text-base font-semibold text-red-700">{T.fail[lang]}</p>}
      {status === "ok" && missing.length > 0 && (
        <p className="mt-2 text-base font-semibold text-amber-800">
          {T.missing[lang]} {missing.join(", ")}
        </p>
      )}
      {status === "ok" && missing.length === 0 && (
        <p className="mt-2 text-base font-semibold text-emerald-800">{T.allSet[lang]}</p>
      )}
    </section>
  );
}
