"use client";

import { useState } from "react";
import { api, type ConstituencyOut } from "@/lib/api";

export function FeedbackForm({
  constituencies,
  preselectedConstituencyId,
}: {
  constituencies: ConstituencyOut[];
  preselectedConstituencyId?: number;
}) {
  const [text, setText] = useState("");
  const [constituencyId, setConstituencyId] = useState<string>(
    preselectedConstituencyId ? String(preselectedConstituencyId) : ""
  );
  const [language, setLanguage] = useState("en");
  const [status, setStatus] = useState<"idle" | "sending" | "ok" | "err">("idle");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (text.trim().length < 4) {
      setError("Please write at least a few words.");
      return;
    }
    setStatus("sending");
    setError(null);
    try {
      await api.submitFeedback({
        text: text.trim(),
        language,
        constituency_id: constituencyId ? Number(constituencyId) : undefined,
      });
      setStatus("ok");
      setText("");
    } catch (e) {
      setStatus("err");
      setError(e instanceof Error ? e.message : "Failed to submit.");
    }
  }

  if (status === "ok") {
    return (
      <div className="border border-green/30 bg-green-soft px-4 py-5 rounded-sm">
        <p className="font-display font-semibold text-green text-lg">Thank you.</p>
        <p className="text-sm text-ink-soft mt-1">
          Your feedback is queued for moderation. Once approved it will be added to the relevant cluster.
        </p>
        <button
          onClick={() => setStatus("idle")}
          className="mt-4 text-xs uppercase tracking-wideish text-ashoka hover:text-ashoka-deep"
        >
          Submit another →
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="constituency" className="label-caps block mb-1.5">
          Constituency (optional)
        </label>
        <select
          id="constituency"
          value={constituencyId}
          onChange={(e) => setConstituencyId(e.target.value)}
          className="w-full bg-paper-deep border border-paper-line text-sm py-2 px-3 outline-none focus:border-ashoka rounded-sm"
        >
          <option value="">— Select —</option>
          {constituencies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="text" className="label-caps block mb-1.5">
          What would you like to share?
        </label>
        <textarea
          id="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          maxLength={2000}
          className="w-full bg-paper-deep border border-paper-line text-sm py-2 px-3 outline-none focus:border-ashoka rounded-sm leading-relaxed"
          placeholder="Describe an issue, response to a scheme, or local observation…"
        />
        <p className="text-[11px] text-ink-muted mt-1">{text.length}/2000</p>
      </div>

      <div>
        <label htmlFor="language" className="label-caps block mb-1.5">Language</label>
        <select
          id="language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="bg-paper-deep border border-paper-line text-sm py-2 px-3 outline-none focus:border-ashoka rounded-sm"
        >
          <option value="en">English</option>
          <option value="hi">हिन्दी (Hindi)</option>
        </select>
      </div>

      {error && <p className="text-sm text-saffron">{error}</p>}

      <button
        type="submit"
        disabled={status === "sending"}
        className="bg-ink text-paper px-5 py-2.5 text-sm uppercase tracking-wideish font-medium hover:bg-ashoka transition-colors disabled:opacity-50"
      >
        {status === "sending" ? "Submitting…" : "Submit feedback"}
      </button>
    </form>
  );
}
