"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

export function LanguageToggle({
  currentLang,
  availableLangs,
}: {
  currentLang: string;
  availableLangs: string[];
}) {
  const pathname = usePathname();
  const params = useSearchParams();

  function url(lang: string) {
    const sp = new URLSearchParams(params.toString());
    sp.set("lang", lang);
    return `${pathname}?${sp.toString()}`;
  }

  const langs = ["en", "hi"].filter((l) => availableLangs.includes(l));
  if (langs.length < 2) return null;

  return (
    <div className="flex items-center gap-2 text-[11px] uppercase tracking-wideish font-medium">
      {langs.map((l, i) => (
        <span key={l} className="flex items-center gap-2">
          <Link
            href={url(l)}
            className={l === currentLang ? "text-ink underline underline-offset-4 decoration-ashoka" : "text-ink-muted hover:text-ink"}
          >
            {l === "en" ? "English" : "हिन्दी"}
          </Link>
          {i === 0 && <span className="text-paper-line">·</span>}
        </span>
      ))}
    </div>
  );
}
