"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Lang = "mr" | "hi" | "en";

const T = {
  title: { mr: "रोज सकाळी सल्ला मिळवा", hi: "रोज सुबह सलाह पाएं", en: "Get this advice every morning" },
  push: { mr: "🔔 फोनवर सूचना चालू करा", hi: "🔔 फोन पर सूचना चालू करें", en: "🔔 Turn on phone notifications" },
  pushOn: { mr: "✔ सूचना चालू आहेत", hi: "✔ सूचना चालू हैं", en: "✔ Notifications are on" },
  pushOff: { mr: "बंद करा", hi: "बंद करें", en: "Turn off" },
  pushDenied: {
    mr: "सूचना बंद आहेत. फोन सेटिंग्जमध्ये या साइटसाठी सूचनांना परवानगी द्या.",
    hi: "सूचनाएं बंद हैं। फोन सेटिंग में इस साइट के लिए सूचनाएं चालू करें।",
    en: "Notifications are blocked. Allow them for this site in your phone settings.",
  },
  pushIos: {
    mr: "आयफोनवर: Safari मधील शेअर बटण दाबा → 'Add to Home Screen' करा, मग तेथून हे अॅप उघडून सूचना चालू करा.",
    hi: "आईफोन पर: Safari में शेयर बटन दबाएं → 'Add to Home Screen' करें, फिर वहां से खोलकर सूचना चालू करें।",
    en: "On iPhone: tap Share in Safari → 'Add to Home Screen', then open the app from there to turn on notifications.",
  },
  pushFail: {
    mr: "सूचना चालू करता आल्या नाहीत. पुन्हा प्रयत्न करा.",
    hi: "सूचना चालू नहीं हो सकीं। फिर कोशिश करें।",
    en: "Couldn't turn on notifications. Please try again.",
  },
  phoneLabel: {
    mr: "WhatsApp / SMS वर हवे? मोबाईल नंबर टाका",
    hi: "WhatsApp / SMS पर चाहिए? मोबाइल नंबर डालें",
    en: "Want it on WhatsApp / SMS? Enter your mobile number",
  },
  consent: {
    mr: "मला या नंबरवर रोज सल्ला (WhatsApp/SMS) आणि फोन कॉल मिळण्यास माझी संमती आहे.",
    hi: "मैं इस नंबर पर रोज सलाह (WhatsApp/SMS) और फोन कॉल पाने की सहमति देता/देती हूं।",
    en: "I agree to get daily advice (WhatsApp/SMS) and a voice call on this number.",
  },
  register: { mr: "नोंदणी करा", hi: "रजिस्टर करें", en: "Register" },
  registered: { mr: "✔ नोंदणी झाली! उद्यापासून सकाळी सल्ला मिळेल.", hi: "✔ रजिस्टर हो गया! कल सुबह से सलाह मिलेगी।", en: "✔ Registered! You'll get advice every morning." },
  already: { mr: "✔ हा नंबर आधीच नोंदणीकृत आहे.", hi: "✔ यह नंबर पहले से रजिस्टर है।", en: "✔ This number is already registered." },
  badPhone: { mr: "कृपया १० अंकी मोबाईल नंबर टाका.", hi: "कृपया 10 अंकों का मोबाइल नंबर डालें।", en: "Please enter a 10-digit mobile number." },
  needConsent: { mr: "कृपया संमतीवर खूण करा.", hi: "कृपया सहमति पर टिक करें।", en: "Please tick the consent box." },
  regFail: { mr: "नोंदणी झाली नाही. पुन्हा प्रयत्न करा.", hi: "रजिस्टर नहीं हो सका। फिर कोशिश करें।", en: "Registration failed. Please try again." },
  missed: {
    mr: "📞 स्मार्टफोन नाही? या नंबरवर मिस्ड कॉल द्या — आम्ही तुम्हाला परत फोन करून आजचा सल्ला ऐकवू:",
    hi: "📞 स्मार्टफोन नहीं है? इस नंबर पर मिस्ड कॉल दें — हम वापस फोन करके आज की सलाह सुनाएंगे:",
    en: "📞 No smartphone? Give a missed call to this number — we'll call you back with today's advice:",
  },
} as const;

const PUSH_KEY = "kisan_push_v1";
const PHONE_KEY = "kisan_registered_v1";
const MISSED_CALL_NUMBER = process.env.NEXT_PUBLIC_MISSED_CALL_NUMBER || "";

export interface AlertContext {
  lang: Lang;
  cropId: string;
  das: number;
  latitude: number;
  longitude: number;
  district?: string;
}

function urlBase64ToUint8Array(base64: string): Uint8Array<ArrayBuffer> {
  const padded = (base64 + "=".repeat((4 - (base64.length % 4)) % 4)).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(padded);
  const out = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

function readFlag(key: string): boolean {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}
function writeFlag(key: string, on: boolean) {
  try {
    if (on) localStorage.setItem(key, "1");
    else localStorage.removeItem(key);
  } catch {}
}

export function DailyAlerts({ ctx }: { ctx: AlertContext }) {
  const { lang } = ctx;
  const [pushAvailable, setPushAvailable] = useState(false); // server has VAPID keys and browser supports push
  const [needsInstall, setNeedsInstall] = useState(false); // iPhone Safari tab: push only works once installed
  const [pushOn, setPushOn] = useState(false);
  const [pushMsg, setPushMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const [phone, setPhone] = useState("");
  const [consent, setConsent] = useState(false);
  const [phoneMsg, setPhoneMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    setPushOn(readFlag(PUSH_KEY));
    setRegistered(readFlag(PHONE_KEY));

    const ua = navigator.userAgent;
    const isIos = /iPhone|iPad|iPod/.test(ua);
    const standalone =
      window.matchMedia?.("(display-mode: standalone)").matches ||
      (navigator as unknown as { standalone?: boolean }).standalone === true;
    const supported = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;

    if (isIos && !standalone) {
      setNeedsInstall(true);
    }
    if (!supported) return;
    api
      .getPushConfig()
      .then((c) => setPushAvailable(c.enabled))
      .catch(() => setPushAvailable(false));
  }, []);

  const enablePush = async () => {
    setBusy(true);
    setPushMsg("");
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setPushMsg(T.pushDenied[lang]);
        return;
      }
      const cfg = await api.getPushConfig();
      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;
      const sub =
        (await reg.pushManager.getSubscription()) ||
        (await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(cfg.public_key),
        }));
      const json = sub.toJSON();
      await api.pushSubscribe({
        endpoint: sub.endpoint,
        keys: { p256dh: json.keys?.p256dh || "", auth: json.keys?.auth || "" },
        language: lang,
        latitude: ctx.latitude,
        longitude: ctx.longitude,
        crop_id: ctx.cropId,
        das: ctx.das,
      });
      writeFlag(PUSH_KEY, true);
      setPushOn(true);
    } catch {
      setPushMsg(T.pushFail[lang]);
    } finally {
      setBusy(false);
    }
  };

  const disablePush = async () => {
    setBusy(true);
    try {
      const reg = await navigator.serviceWorker.getRegistration("/sw.js");
      const sub = await reg?.pushManager.getSubscription();
      if (sub) {
        await api.pushUnsubscribe(sub.endpoint).catch(() => {});
        await sub.unsubscribe();
      }
      writeFlag(PUSH_KEY, false);
      setPushOn(false);
    } finally {
      setBusy(false);
    }
  };

  const registerPhone = async () => {
    const digits = phone.replace(/\D/g, "").replace(/^(91|0)(?=\d{10}$)/, "");
    if (!/^[6-9]\d{9}$/.test(digits)) return setPhoneMsg({ ok: false, text: T.badPhone[lang] });
    if (!consent) return setPhoneMsg({ ok: false, text: T.needConsent[lang] });

    setBusy(true);
    setPhoneMsg(null);
    try {
      const sowing = new Date(Date.now() - ctx.das * 86400000).toISOString().slice(0, 10);
      await api.registerFarmer({
        full_name: "Farmer",
        phone_number: digits,
        language: lang,
        latitude: ctx.latitude,
        longitude: ctx.longitude,
        district: ctx.district,
        crop_id: ctx.cropId,
        sowing_date: sowing,
        consent_sms: true,
        consent_voice: true,
      });
      writeFlag(PHONE_KEY, true);
      setRegistered(true);
      setPhoneMsg({ ok: true, text: T.registered[lang] });
    } catch (e) {
      const text = e instanceof Error ? e.message : "";
      if (/already registered/i.test(text)) {
        writeFlag(PHONE_KEY, true);
        setRegistered(true);
        setPhoneMsg({ ok: true, text: T.already[lang] });
      } else {
        setPhoneMsg({ ok: false, text: T.regFail[lang] });
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-3xl border-2 border-emerald-300 bg-white p-5 space-y-4">
      <h3 className="text-xl font-extrabold text-emerald-950">{T.title[lang]}</h3>

      {needsInstall ? (
        <p className="text-base text-slate-700 bg-amber-50 border border-amber-300 rounded-2xl p-3">{T.pushIos[lang]}</p>
      ) : (
        pushAvailable &&
        (pushOn ? (
          <div className="flex items-center justify-between gap-3">
            <span className="text-lg font-bold text-emerald-800">{T.pushOn[lang]}</span>
            <button
              onClick={disablePush}
              disabled={busy}
              className="h-11 px-4 rounded-xl border-2 border-slate-300 text-base font-bold active:scale-95 disabled:opacity-50"
            >
              {T.pushOff[lang]}
            </button>
          </div>
        ) : (
          <button
            onClick={enablePush}
            disabled={busy}
            className="w-full h-14 rounded-2xl bg-emerald-600 text-white text-lg font-extrabold active:scale-[0.98] disabled:opacity-50"
          >
            {T.push[lang]}
          </button>
        ))
      )}
      {pushMsg && <p className="text-base font-semibold text-red-700">{pushMsg}</p>}

      <div className="space-y-3">
        <label className="block text-base font-bold text-slate-800" htmlFor="kisan-phone">
          {T.phoneLabel[lang]}
        </label>
        {registered ? (
          <p className="text-lg font-bold text-emerald-800">{phoneMsg?.text || T.already[lang]}</p>
        ) : (
          <>
            <input
              id="kisan-phone"
              type="tel"
              inputMode="numeric"
              autoComplete="tel-national"
              placeholder="98XXXXXXXX"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full h-14 rounded-2xl border-2 border-slate-300 bg-white px-4 text-xl font-semibold tracking-wide"
            />
            <label className="flex items-start gap-3 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 h-5 w-5 shrink-0"
              />
              <span>{T.consent[lang]}</span>
            </label>
            <button
              onClick={registerPhone}
              disabled={busy}
              className="w-full h-14 rounded-2xl bg-white border-2 border-emerald-500 text-emerald-900 text-lg font-extrabold active:scale-[0.98] disabled:opacity-50"
            >
              {T.register[lang]}
            </button>
            {phoneMsg && (
              <p className={`text-base font-semibold ${phoneMsg.ok ? "text-emerald-800" : "text-red-700"}`}>{phoneMsg.text}</p>
            )}
          </>
        )}
      </div>

      {MISSED_CALL_NUMBER && (
        <p className="text-base text-slate-700">
          {T.missed[lang]}{" "}
          <a href={`tel:${MISSED_CALL_NUMBER}`} className="font-extrabold text-emerald-800 underline">
            {MISSED_CALL_NUMBER}
          </a>
        </p>
      )}
    </section>
  );
}
