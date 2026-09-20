"use client";

import { FormEvent, useState } from "react";

import { api } from "@/lib/api";

type Citation = {
  document_id: string;
  document_name: string;
  page: number | null;
  section: string | null;
  snippet: string;
};

type Answer = {
  answer: string;
  citations: Citation[];
  retrieved_chunks: number;
  supported: boolean;
};

export function AskPanel() {
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setPending(true);
    setError("");
    setAnswer(null);
    try {
      setAnswer(
        await api<Answer>("/ask", {
          method: "POST",
          body: JSON.stringify({ question: data.get("question") }),
        }),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not generate an answer");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="mt-14 border border-black/15 bg-[var(--forest)] p-6 text-white md:p-9">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-orange-300">Grounded search</p>
      <h2 className="mt-3 text-3xl font-black tracking-tight">Ask your documents</h2>
      <form className="mt-7 flex flex-col gap-3 md:flex-row" onSubmit={ask}>
        <input className="min-w-0 flex-1 bg-white px-5 py-4 text-[var(--ink)] outline-none" name="question" placeholder="What risks were identified in the report?" minLength={2} required />
        <button className="bg-[var(--accent)] px-7 py-4 font-bold disabled:opacity-60" disabled={pending}>{pending ? "Searching…" : "Ask Locus"}</button>
      </form>
      {error && <p className="mt-5 bg-red-950/50 p-4 text-red-100">{error}</p>}
      {answer && (
        <div className="mt-8 border-t border-white/20 pt-8">
          <p className="text-xl leading-8">{answer.answer}</p>
          <p className="mt-3 text-xs text-white/50">{answer.retrieved_chunks} passages reviewed</p>
          {answer.citations.length > 0 && (
            <div className="mt-7 grid gap-3 md:grid-cols-2">
              {answer.citations.map((citation, index) => (
                <details className="bg-white/10 p-4" key={`${citation.document_id}-${index}`}>
                  <summary className="cursor-pointer font-bold">[{index + 1}] {citation.document_name}{citation.page ? ` · p. ${citation.page}` : ""}</summary>
                  <p className="mt-3 text-sm leading-6 text-white/70">{citation.snippet}</p>
                </details>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

