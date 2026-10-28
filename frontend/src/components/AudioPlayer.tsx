"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Play, Pause, Volume2, RotateCcw, Sparkles } from "lucide-react";

interface AudioPlayerProps {
  audioUrl?: string;
  language?: string;
  label?: string;
  text?: string;
}

export function AudioPlayer({
  audioUrl,
  language = "hi",
  label = "Voice Advisory Preview",
  text,
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceName, setSelectedVoiceName] = useState<string>("");
  const [speechSupported, setSpeechSupported] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<any>(null);

  // Initialize Web Speech API voices
  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      setSpeechSupported(true);

      const updateVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          setAvailableVoices(voices);

          // Select best female voice for current language
          const targetLang = language === "mr" ? "mr" : language === "hi" ? "hi" : "en";
          const langMatch = voices.filter(
            (v) =>
              v.lang.toLowerCase().startsWith(targetLang) ||
              v.lang.toLowerCase().includes(targetLang)
          );

          // Prefer female sounding voice
          const femaleMatch = langMatch.find(
            (v) =>
              v.name.toLowerCase().includes("female") ||
              v.name.toLowerCase().includes("swara") ||
              v.name.toLowerCase().includes("aarohi") ||
              v.name.toLowerCase().includes("kalpana") ||
              v.name.toLowerCase().includes("heera") ||
              v.name.toLowerCase().includes("samantha") ||
              v.name.toLowerCase().includes("zira") ||
              v.name.toLowerCase().includes("google")
          );

          const chosen = femaleMatch || langMatch[0] || voices[0];
          if (chosen) setSelectedVoiceName(chosen.name);
        }
      };

      updateVoices();
      window.speechSynthesis.onvoiceschanged = updateVoices;

      return () => {
        if ("speechSynthesis" in window) {
          window.speechSynthesis.cancel();
        }
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }
  }, [language]);

  // Full URL resolution for audio file fallback
  const resolvedUrl = audioUrl
    ? audioUrl.startsWith("http")
      ? audioUrl
      : `http://localhost:8000${audioUrl}`
    : "";

  const cleanTextForSpeech = (rawText: string) => {
    return rawText
      .replace(/^किसान साथी:|^किसानसाथी:|^KisanSaathi:|^Kisan Saathi:/i, "")
      .replace(/[•\*\_\#]/g, " ")
      .trim();
  };

  const stopPlayback = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    if (audioRef.current) {
      audioRef.current.pause();
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setIsPlaying(false);
  }, []);

  const startSpeech = () => {
    if (!text || typeof window === "undefined" || !("speechSynthesis" in window)) {
      // Fall back to audio element if speech synthesis is unavailable
      if (audioRef.current && resolvedUrl) {
        audioRef.current.play().catch((e) => console.log(e));
        setIsPlaying(true);
      }
      return;
    }

    window.speechSynthesis.cancel();
    const spokenText = cleanTextForSpeech(text);
    const utterance = new SpeechSynthesisUtterance(spokenText);

    // Set language code
    const langCode = language === "mr" ? "mr-IN" : language === "hi" ? "hi-IN" : "en-IN";
    utterance.lang = langCode;

    // Female voice attributes
    utterance.pitch = 1.05; // Slightly elevated warm pitch for pleasant female tone
    utterance.rate = 0.92; // Deliberate, clear pacing for agricultural comprehension

    // Pick female voice if available
    const chosenVoice = availableVoices.find((v) => v.name === selectedVoiceName) ||
      availableVoices.find((v) => v.lang.toLowerCase().includes(language === "mr" ? "mr" : "hi")) ||
      availableVoices.find((v) => v.name.toLowerCase().includes("female"));

    if (chosenVoice) {
      utterance.voice = chosenVoice;
    }

    // Estimate duration based on word count (~130 words per minute)
    const words = spokenText.split(/\s+/).length;
    const estimatedSec = Math.max(3, Math.round((words / 130) * 60));
    setDuration(estimatedSec);
    setCurrentTime(0);

    utterance.onstart = () => {
      setIsPlaying(true);
      const startTime = Date.now();
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        setCurrentTime(Math.min(elapsed, estimatedSec));
      }, 200);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setCurrentTime(estimatedSec);
      if (timerRef.current) clearInterval(timerRef.current);
    };

    utterance.onerror = (e) => {
      console.warn("SpeechSynthesis error:", e);
      setIsPlaying(false);
      if (timerRef.current) clearInterval(timerRef.current);
      // Fallback to audio element
      if (audioRef.current && resolvedUrl) {
        audioRef.current.play().catch(() => {});
      }
    };

    window.speechSynthesis.speak(utterance);
  };

  const togglePlay = () => {
    if (isPlaying) {
      stopPlayback();
    } else {
      startSpeech();
    }
  };

  const restartAudio = () => {
    stopPlayback();
    setCurrentTime(0);
    setTimeout(() => {
      startSpeech();
    }, 150);
  };

  const formatTime = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  const langBadges: Record<string, { label: string; color: string }> = {
    hi: { label: "Hindi (हिंदी)", color: "bg-orange-50 text-orange-700 border-orange-200" },
    mr: { label: "Marathi (मराठी)", color: "bg-indigo-50 text-indigo-700 border-indigo-200" },
    en: { label: "English", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  };
  const badge = langBadges[language] || langBadges["hi"];

  return (
    <div className="bg-gradient-to-br from-[#051c14] to-[#0a2e21] text-white rounded-3xl p-5 shadow-xl border border-emerald-600/30">
      {/* Hidden fallback audio tag */}
      <audio
        ref={audioRef}
        src={resolvedUrl}
        onEnded={() => setIsPlaying(false)}
        onError={() => {}}
      />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center justify-center shadow-inner relative">
            <Volume2 className="w-5 h-5" />
            {isPlaying && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-ping" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold tracking-tight text-white">{label}</h4>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300 border border-emerald-400/30 flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5" />
                Lady Voice (Kisan Sakhi)
              </span>
            </div>
            <p className="text-[11px] text-emerald-200/70">
              Clear vernacular speech • {language === "mr" ? "मराठी स्पष्ट उच्चार" : language === "hi" ? "हिंदी स्पष्ट वाणी" : "Natural Voice Stream"}
            </p>
          </div>
        </div>

        <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border shadow-xs ${badge.color}`}>
          {badge.label}
        </span>
      </div>

      {/* Voice Speaking Audio Visualizer */}
      {isPlaying && (
        <div className="mb-3 p-2.5 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-between text-xs text-emerald-300">
          <span className="flex items-center gap-2 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Speaking advisory in native voice...
          </span>
          <div className="flex items-center gap-1 h-4">
            <span className="w-1 bg-emerald-400 h-2 animate-[bounce_0.6s_infinite]"></span>
            <span className="w-1 bg-emerald-400 h-4 animate-[bounce_0.8s_infinite]"></span>
            <span className="w-1 bg-emerald-400 h-3 animate-[bounce_0.7s_infinite]"></span>
            <span className="w-1 bg-emerald-400 h-5 animate-[bounce_0.9s_infinite]"></span>
            <span className="w-1 bg-emerald-400 h-2 animate-[bounce_0.5s_infinite]"></span>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3.5 pt-1">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlay}
          className="w-12 h-12 rounded-2xl bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 text-slate-950 flex items-center justify-center transition shadow-lg shadow-emerald-500/30 shrink-0 cursor-pointer active:scale-95"
          title={isPlaying ? "Pause voice" : "Listen in vernacular female voice"}
        >
          {isPlaying ? (
            <Pause className="w-5 h-5 fill-current" />
          ) : (
            <Play className="w-5 h-5 fill-current ml-0.5" />
          )}
        </button>

        {/* Replay */}
        <button
          onClick={restartAudio}
          className="p-2.5 rounded-xl bg-emerald-950/80 text-emerald-200 hover:text-white hover:bg-emerald-900 border border-emerald-500/20 transition cursor-pointer"
          title="Restart speech from beginning"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Wave / Scrub Bar */}
        <div className="flex-1 flex flex-col gap-1.5">
          <div className="w-full bg-[#051810] h-2.5 rounded-full overflow-hidden relative border border-emerald-900/40">
            <div
              className="bg-gradient-to-r from-emerald-400 to-teal-300 h-full rounded-full transition-all duration-200 shadow-sm"
              style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-[11px] font-mono text-emerald-300/80 font-medium">
            <span>{formatTime(currentTime)}</span>
            <span>{duration > 0 ? formatTime(duration) : "0:15"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
