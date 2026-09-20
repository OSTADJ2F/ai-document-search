const capabilities = [
  ["01", "Private by design", "Every query is scoped to the authenticated owner."],
  ["02", "Evidence attached", "Answers link to the exact source passage and page."],
  ["03", "Hybrid retrieval", "Semantic meaning and precise keywords work together."],
];

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-8 md:px-12 lg:px-20">
      <nav className="mx-auto flex max-w-7xl items-center justify-between border-b border-black/15 pb-5">
        <div className="text-xl font-black tracking-[-0.04em]">LOCUS / AI</div>
        <a className="rounded-full bg-[var(--forest)] px-5 py-2.5 text-sm font-bold text-white" href="/login">
          Open workspace
        </a>
      </nav>

      <section className="mx-auto grid max-w-7xl gap-12 py-20 lg:grid-cols-[1.25fr_0.75fr] lg:py-28">
        <div>
          <p className="mb-6 text-xs font-bold uppercase tracking-[0.25em] text-[var(--accent)]">
            Document intelligence, with receipts
          </p>
          <h1 className="max-w-4xl text-6xl font-black leading-[0.9] tracking-[-0.065em] md:text-8xl">
            Ask your archive. Verify every answer.
          </h1>
          <p className="mt-8 max-w-2xl text-lg leading-8 text-black/65 md:text-xl">
            Upload reports, notes, and research. Locus finds the relevant evidence and responds with
            citations you can inspect—not claims you have to trust.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <a className="bg-[var(--accent)] px-7 py-4 font-bold text-white" href="/register">Create free account</a>
            <a className="border border-black/25 px-7 py-4 font-bold" href="#how">See how it works</a>
          </div>
        </div>

        <div className="self-end border border-black/15 bg-white/50 p-6 shadow-[12px_12px_0_#173f35]">
          <div className="mb-10 flex items-center justify-between text-xs font-bold uppercase tracking-widest">
            <span>Live evidence</span><span className="text-emerald-700">● Ready</span>
          </div>
          <p className="text-2xl font-bold leading-tight">“What are the top operational risks?”</p>
          <p className="mt-5 leading-7 text-black/65">
            Supply-chain concentration and delayed regulatory approvals were identified as the
            highest-impact operational risks.
          </p>
          <div className="mt-6 border-l-4 border-[var(--accent)] bg-[var(--paper)] p-4 text-sm">
            <strong>Annual report · p. 14</strong><br />“Primary exposure remains supplier concentration…”
          </div>
        </div>
      </section>

      <section id="how" className="mx-auto grid max-w-7xl border-y border-black/15 md:grid-cols-3">
        {capabilities.map(([number, title, copy]) => (
          <article className="border-black/15 p-8 md:border-r last:md:border-r-0" key={number}>
            <span className="text-sm font-black text-[var(--accent)]">{number}</span>
            <h2 className="mt-8 text-2xl font-black tracking-tight">{title}</h2>
            <p className="mt-3 leading-7 text-black/60">{copy}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

