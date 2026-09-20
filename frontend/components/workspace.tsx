"use client";

import { ChangeEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { formatFileSize } from "@/lib/format";
import { AskPanel } from "@/components/ask-panel";

type Document = {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: "uploaded" | "processing" | "ready" | "failed" | "deleted";
  error_message: string | null;
  created_at: string;
};

const statusStyle: Record<Document["status"], string> = {
  uploaded: "bg-amber-100 text-amber-800",
  processing: "bg-blue-100 text-blue-800",
  ready: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
  deleted: "bg-black/10 text-black/60",
};

export function Workspace() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const result = await api<{ items: Document[] }>("/documents");
      setDocuments(result.items);
    } catch (reason) {
      if (reason instanceof Error && "status" in reason && reason.status === 401) router.push("/login");
      else setError(reason instanceof Error ? reason.message : "Could not load documents");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    const interval = window.setInterval(() => void load(), 5_000);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, [load]);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    try {
      await api<Document>("/documents", { method: "POST", body });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload failed");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this document? This removes its uploaded file.")) return;
    await api(`/documents/${id}`, { method: "DELETE" });
    setDocuments((items) => items.filter((item) => item.id !== id));
  }

  function logout() {
    localStorage.removeItem("access_token");
    router.push("/login");
  }

  return (
    <main className="min-h-screen px-6 py-8 md:px-12">
      <nav className="mx-auto flex max-w-7xl items-center justify-between border-b border-black/15 pb-5">
        <div className="text-xl font-black tracking-[-0.04em]">LOCUS / WORKSPACE</div>
        <button className="text-sm font-bold text-black/60 hover:text-black" onClick={logout}>Log out</button>
      </nav>
      <section className="mx-auto max-w-7xl py-14">
        <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--accent)]">Your evidence library</p>
            <h1 className="mt-3 text-5xl font-black tracking-[-0.05em] md:text-6xl">Documents</h1>
            <p className="mt-4 max-w-xl leading-7 text-black/60">Upload PDF, Markdown, or UTF-8 text files. Processing status updates appear here.</p>
          </div>
          <label className="cursor-pointer bg-[var(--forest)] px-6 py-4 text-center font-bold text-white">
            {uploading ? "Uploading…" : "+ Upload document"}
            <input className="sr-only" disabled={uploading} onChange={upload} type="file" accept=".pdf,.txt,.md,.markdown" />
          </label>
        </div>
        {error && <p className="mt-8 border-l-4 border-red-600 bg-red-50 p-4 text-red-800">{error}</p>}
        <div className="mt-12 overflow-hidden border border-black/15 bg-white/50">
          {loading ? (
            <p className="p-10 text-black/55">Loading your library…</p>
          ) : documents.length === 0 ? (
            <div className="p-12 text-center"><p className="text-2xl font-black">Your library is empty</p><p className="mt-2 text-black/55">Upload the first document to begin.</p></div>
          ) : (
            documents.map((document) => (
              <article className="grid gap-4 border-b border-black/10 p-5 last:border-0 md:grid-cols-[1fr_auto_auto] md:items-center" key={document.id}>
                <div><h2 className="font-bold">{document.filename}</h2><p className="mt-1 text-sm text-black/50">{document.file_type.toUpperCase()} · {formatFileSize(document.file_size)}</p></div>
                <span className={`w-fit rounded-full px-3 py-1 text-xs font-bold capitalize ${statusStyle[document.status]}`}>{document.status}</span>
                <button className="text-left text-sm font-bold text-red-700 md:text-right" onClick={() => void remove(document.id)}>Delete</button>
                {document.error_message && <p className="text-sm text-red-700 md:col-span-3">{document.error_message}</p>}
              </article>
            ))
          )}
        </div>
        <AskPanel />
      </section>
    </main>
  );
}
