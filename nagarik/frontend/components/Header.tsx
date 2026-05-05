import Link from "next/link";

const NAV = [
  { href: "/", label: "Today" },
  { href: "/constituencies", label: "Constituencies" },
  { href: "/feedback", label: "Citizen Voice" },
  { href: "/admin", label: "Admin" },
];

export function Header() {
  return (
    <header className="border-b border-paper-line bg-paper">
      {/* Top strip: tiny meta line, like a newspaper */}
      <div className="border-b border-paper-line/70">
        <div className="max-w-6xl mx-auto px-6 py-2 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-ink-muted">
          <span>A nonpartisan civic intelligence platform</span>
          <span className="font-mono normal-case tracking-wider">
            Vol. I · Issue 001 · {new Date().toLocaleDateString("en-IN", {
              day: "numeric", month: "long", year: "numeric",
            })}
          </span>
        </div>
      </div>

      {/* Masthead */}
      <div className="max-w-6xl mx-auto px-6 pt-8 pb-4 flex items-end justify-between">
        <Link href="/" className="block">
          <h1 className="font-display font-semibold text-[3.5rem] leading-[0.95] tracking-tightish">
            Nagarik
          </h1>
          <p className="text-xs text-ink-muted mt-1 font-mono tracking-wider">
            नागरिक  ·  the citizen
          </p>
        </Link>
        <p className="hidden md:block text-xs text-ink-muted max-w-xs text-right leading-relaxed">
          Government updates, decoded for the people they affect.
          Every claim links back to its source.
        </p>
      </div>

      {/* Navigation row */}
      <nav className="max-w-6xl mx-auto px-6 py-3 border-t border-b border-ink/90 flex flex-wrap gap-x-8 gap-y-2 text-sm">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="text-ink-soft hover:text-ashoka transition-colors font-medium"
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
