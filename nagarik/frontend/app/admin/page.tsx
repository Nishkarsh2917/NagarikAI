import { AdminPanel } from "./AdminPanel";

export const dynamic = "force-dynamic";

export default function AdminPage() {
  return (
    <div>
      <header className="ruled pt-3 mb-10">
        <p className="ident">Admin</p>
        <h1 className="font-display font-semibold text-4xl md:text-5xl mt-2 tracking-tightish">
          Ingestion control panel.
        </h1>
        <p className="mt-3 text-ink-soft max-w-column leading-relaxed">
          Token-gated. The same admin token configured in the backend&apos;s
          <code className="font-mono text-xs mx-1 px-1 bg-paper-deep rounded-sm">.env</code>
          unlocks this view.
        </p>
      </header>
      <AdminPanel />
    </div>
  );
}
