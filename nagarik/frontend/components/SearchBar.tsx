"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function SearchBar({ initialValue = "" }: { initialValue?: string }) {
  const router = useRouter();
  const [q, setQ] = useState(initialValue);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim()) router.push(`/?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <form onSubmit={onSubmit} className="flex items-stretch border-b border-ink/80 max-w-xl">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search updates, schemes, bills…"
        className="flex-1 bg-transparent py-3 text-ink placeholder:text-ink-muted outline-none text-base"
      />
      <button
        type="submit"
        className="px-4 text-xs uppercase tracking-wideish font-medium text-ashoka hover:text-ashoka-deep"
      >
        Search →
      </button>
    </form>
  );
}
