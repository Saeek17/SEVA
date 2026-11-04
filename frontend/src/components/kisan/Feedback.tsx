"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type Lang = "mr" | "hi" | "en";

const T = {
  ask: { mr: "हा सल्ला उपयोगी होता का?", hi: "क्या यह सलाह काम की थी?", en: "Was this advice useful?" },
  thanks: { mr: "धन्यवाद! 🙏", hi: "धन्यवाद! 🙏", en: "Thank you! 🙏" },
} as const;

export interface FeedbackCtx {
  lang: Lang;
  cropId: string;
  action: string;
  reasonCode?: string;
  das?: number;
}

export function Feedback({ ctx }: { ctx: FeedbackCtx }) {
  const [sent, setSent] = useState(false);

  async function send(helpful: boolean) {
    setSent(true); // thank the farmer straight away; a failed send is not worth bothering them with
    try {
      await api.sendFeedback({
        helpful,
        crop_id: ctx.cropId,
        action: ctx.action,
        reason_code: ctx.reasonCode || undefined,
        das: ctx.das,
        language: ctx.lang,
      });
    } catch {
      /* anonymous and best-effort */
    }
  }

  if (sent) {
    return <p className="text-center text-lg font-bold text-emerald-800">{T.thanks[ctx.lang]}</p>;
  }
  return (
    <section className="rounded-2xl border-2 border-slate-200 bg-white p-4">
      <p className="text-base font-bold text-slate-700 text-center">{T.ask[ctx.lang]}</p>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <button
          onClick={() => send(true)}
          aria-label="Helpful"
          className="h-14 rounded-2xl bg-emerald-50 border-2 border-emerald-400 text-3xl active:scale-95"
        >
          👍
        </button>
        <button
          onClick={() => send(false)}
          aria-label="Not helpful"
          className="h-14 rounded-2xl bg-rose-50 border-2 border-rose-300 text-3xl active:scale-95"
        >
          👎
        </button>
      </div>
    </section>
  );
}
