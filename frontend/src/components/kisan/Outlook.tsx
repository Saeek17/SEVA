"use client";

import type { DayOutlook } from "@/lib/types";

type Lang = "mr" | "hi" | "en";

const TITLE = { mr: "पुढचे ५ दिवस", hi: "अगले 5 दिन", en: "Next 5 days" } as const;
const DAYS: Record<Lang, string[]> = {
  mr: ["रवि", "सोम", "मंगळ", "बुध", "गुरु", "शुक्र", "शनि"],
  hi: ["रवि", "सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि"],
  en: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
};

function icon(d: DayOutlook): string {
  if (d.rain_mm >= 10) return "⛈️";
  if (d.rain_mm >= 2 || d.rain_prob_pct >= 60) return "🌧️";
  if (d.max_temp_c >= 38) return "🔥";
  if (d.rain_prob_pct >= 30) return "⛅";
  return "☀️";
}

// Date strings are YYYY-MM-DD; parse as local noon so the weekday never shifts with the timezone.
function weekday(date: string, lang: Lang): string {
  const dt = new Date(`${date}T12:00:00`);
  return Number.isNaN(dt.getTime()) ? "" : DAYS[lang][dt.getDay()];
}

export function Outlook({ days, lang }: { days?: DayOutlook[]; lang: Lang }) {
  if (!days || days.length === 0) return null;
  const shown = days.slice(0, 5);
  return (
    <section>
      <h3 className="text-base font-bold text-slate-600 mb-2">{TITLE[lang]}</h3>
      <div className="grid grid-cols-5 gap-2">
        {shown.map((d) => (
          <div
            key={d.date}
            className="rounded-2xl border-2 border-slate-200 bg-white px-1 py-2 text-center"
          >
            <div className="text-sm font-bold text-slate-600">{weekday(d.date, lang)}</div>
            <div className="text-3xl leading-tight my-1">{icon(d)}</div>
            <div className="text-base font-extrabold text-slate-900">{Math.round(d.max_temp_c)}°</div>
            <div className="text-xs font-semibold text-slate-500">{Math.round(d.min_temp_c)}°</div>
            <div className="mt-1 text-xs font-bold text-sky-700">💧 {Math.round(d.rain_mm)} mm</div>
          </div>
        ))}
      </div>
    </section>
  );
}
