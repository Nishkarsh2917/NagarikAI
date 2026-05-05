import type { TrustLabel } from "@/lib/api";

const LABEL_STYLES: Record<TrustLabel, { dot: string; text: string; bg: string }> = {
  official:    { dot: "bg-green",   text: "text-green",   bg: "bg-green-soft" },
  third_party: { dot: "bg-ashoka",  text: "text-ashoka",  bg: "bg-ashoka-soft" },
  tentative:   { dot: "bg-saffron", text: "text-saffron", bg: "bg-saffron-soft" },
};

const LABEL_TEXT: Record<TrustLabel, string> = {
  official: "Official source",
  third_party: "Third-party source",
  tentative: "Tentative",
};

export function SourceLabel({ label }: { label: TrustLabel | null | undefined }) {
  if (!label) return null;
  const s = LABEL_STYLES[label];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[11px] font-medium ${s.bg} ${s.text} uppercase tracking-wideish`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} aria-hidden />
      {LABEL_TEXT[label]}
    </span>
  );
}

export function ConfidenceBadge({ score }: { score: number }) {
  const bucket: "high" | "medium" | "low" =
    score >= 0.7 ? "high" : score >= 0.4 ? "medium" : "low";
  const styles = {
    high:   { dot: "bg-green",   text: "text-green",   word: "High" },
    medium: { dot: "bg-amber",   text: "text-amber",   word: "Moderate" },
    low:    { dot: "bg-saffron", text: "text-saffron", word: "Low" },
  }[bucket];

  return (
    <span
      title={`Extraction confidence: ${(score * 100).toFixed(0)}%`}
      className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${styles.text} uppercase tracking-wideish`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} aria-hidden />
      {styles.word} confidence
    </span>
  );
}
