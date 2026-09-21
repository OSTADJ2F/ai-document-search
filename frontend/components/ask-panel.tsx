"use client";

import { FormEvent, useEffect, useState } from "react";

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

type Provider = "local" | "groq" | "deepseek";

const PROVIDER_STORAGE_KEY = "locus-ai-provider";
const LOCAL_PORT_STORAGE_KEY = "locus-local-server-port";

export function AskPanel() {
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [provider, setProvider] = useState<Provider>("local");
  const [localServerPort, setLocalServerPort] = useState("8080");

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      const saved = window.localStorage.getItem(PROVIDER_STORAGE_KEY);
      if (saved === "local" || saved === "groq" || saved === "deepseek") {
        setProvider(saved);
      }
      const savedPort = window.localStorage.getItem(LOCAL_PORT_STORAGE_KEY);
      const port = Number(savedPort);
      if (Number.isInteger(port) && port >= 1 && port <= 65535) {
        setLocalServerPort(String(port));
      }
    }, 0);
    return () => window.clearTimeout(timeout);
  }, []);

  function chooseProvider(value: Provider) {
    setProvider(value);
    setAnswer(null);
    setError("");
    window.localStorage.setItem(PROVIDER_STORAGE_KEY, value);
  }

  function chooseLocalPort(value: string) {
    setLocalServerPort(value);
    window.localStorage.setItem(LOCAL_PORT_STORAGE_KEY, value);
  }

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
          body: JSON.stringify({
            question: data.get("question"),
            provider,
            local_server_port: provider === "local" ? Number(localServerPort) : undefined,
          }),
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
      <form className="mt-7" onSubmit={ask}>
        <fieldset>
          <legend className="text-xs font-bold uppercase tracking-[0.16em] text-white/60">AI provider</legend>
          <div className="mt-3 grid items-start gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div className={`border p-4 ${provider === "local" ? "border-orange-300 bg-white/10" : "border-white/20"}`}>
              <label className="cursor-pointer">
                <input className="sr-only" type="radio" name="provider" value="local" checked={provider === "local"} onChange={() => chooseProvider("local")} />
                <span className="block font-bold">Local server</span>
                <span className="mt-1 block text-sm text-white/60">Private llama.cpp model on this machine.</span>
              </label>
              {provider === "local" && (
                <label className="mt-4 block text-xs font-bold uppercase tracking-[0.12em] text-white/70">
                  Port
                  <input className="mt-2 block w-full border border-white/25 bg-white px-3 py-2 text-base font-normal tracking-normal text-[var(--ink)] outline-none focus:border-orange-300" type="number" name="local_server_port" min={1} max={65535} step={1} value={localServerPort} onChange={(event) => chooseLocalPort(event.target.value)} disabled={pending} required />
                </label>
              )}
            </div>
            <label className={`cursor-pointer border p-4 ${provider === "groq" ? "border-orange-300 bg-white/10" : "border-white/20"}`}>
              <input className="sr-only" type="radio" name="provider" value="groq" checked={provider === "groq"} onChange={() => chooseProvider("groq")} />
              <span className="block font-bold">Groq</span>
              <span className="mt-1 block text-sm text-white/60">Sends retrieved passages to Groq. Requires GROQ_API_KEY.</span>
            </label>
            <label className={`cursor-pointer border p-4 ${provider === "deepseek" ? "border-orange-300 bg-white/10" : "border-white/20"}`}>
              <input className="sr-only" type="radio" name="provider" value="deepseek" checked={provider === "deepseek"} onChange={() => chooseProvider("deepseek")} />
              <span className="block font-bold">DeepSeek</span>
              <span className="mt-1 block text-sm text-white/60">Sends retrieved passages to DeepSeek. Requires DEEPSEEK_API_KEY.</span>
            </label>
          </div>
        </fieldset>
        <div className="mt-7 flex flex-col gap-3 md:flex-row">
          <input className="min-w-0 flex-1 bg-white px-5 py-4 text-[var(--ink)] outline-none" name="question" placeholder="What risks were identified in the report?" minLength={2} required />
          <button className="bg-[var(--accent)] px-7 py-4 font-bold disabled:opacity-60" disabled={pending}>{pending ? "Searching…" : "Ask Locus"}</button>
        </div>
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
