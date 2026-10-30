// Turns a spoken sentence like "तूर, लातूर, 45 दिवस" into the three answers the farmer page needs.
// Pure function (no browser APIs) so it can be tested in isolation.

export interface ParseCrop {
  id: string;
  names: string[];
}
export interface ParsePlace {
  id: string;
  names: string[];
}
export interface ParseAge {
  id: string;
  das: number; // -1 = "ready to harvest"
}
export interface ParsedSpeech {
  cropId?: string;
  placeId?: string;
  ageId?: string;
}

const DEVANAGARI_DIGITS = "०१२३४५६७८९";
const READY_WORDS = ["कापणी", "काढणी", "कटाई", "तयार", "ready", "harvest"];
const MONTH_WORDS = ["महिने", "महिना", "महीने", "महीना", "month"];

function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[०-९]/g, (d) => String(DEVANAGARI_DIGITS.indexOf(d)))
    .replace(/[.,;:!?।]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// A name must start a word ("तूर" must not match inside "लातूर"), but may carry a Marathi suffix ("लातूरला").
// Longest match wins.
function bestMatch<T extends { id: string; names: string[] }>(spoken: string, items: T[]): string | undefined {
  const padded = ` ${spoken}`;
  const atWordStart = (needle: string) => padded.includes(` ${needle}`);
  let best: { id: string; len: number } | undefined;
  for (const item of items) {
    for (const raw of item.names) {
      const name = normalize(raw);
      if (!name) continue;
      const stem = name.length >= 5 ? name.slice(0, -1) : name;
      const hit = atWordStart(name) ? name.length : atWordStart(stem) ? stem.length : 0;
      if (hit && (!best || hit > best.len)) best = { id: item.id, len: hit };
    }
  }
  return best?.id;
}

export function parseSpoken(
  text: string,
  options: { crops: ParseCrop[]; places: ParsePlace[]; ages: ParseAge[] }
): ParsedSpeech {
  const spoken = normalize(text);
  const out: ParsedSpeech = {};
  if (!spoken) return out;

  out.cropId = bestMatch(spoken, options.crops);
  out.placeId = bestMatch(spoken, options.places);

  const ready = options.ages.find((a) => a.das === -1);
  if (ready && READY_WORDS.some((w) => spoken.includes(w))) {
    out.ageId = ready.id;
    return out;
  }

  const num = spoken.match(/\d+/);
  if (num) {
    let days = parseInt(num[0], 10);
    if (MONTH_WORDS.some((w) => spoken.includes(w))) days *= 30;
    const buckets = options.ages.filter((a) => a.das > 0);
    if (days > 0 && buckets.length) {
      out.ageId = buckets.reduce((a, b) => (Math.abs(b.das - days) < Math.abs(a.das - days) ? b : a)).id;
    }
  }
  return out;
}
