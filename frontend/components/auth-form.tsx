"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { api, AuthResponse } from "@/lib/api";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const result = await api<AuthResponse>(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({ email: data.get("email"), password: data.get("password") }),
      });
      localStorage.setItem("access_token", result.access_token);
      router.push("/workspace");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Authentication failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="mt-10 space-y-5" onSubmit={submit}>
      <label className="block text-sm font-bold">
        Email
        <input className="mt-2 w-full border border-black/25 bg-white px-4 py-3 outline-none focus:border-[var(--accent)]" name="email" type="email" required />
      </label>
      <label className="block text-sm font-bold">
        Password
        <input className="mt-2 w-full border border-black/25 bg-white px-4 py-3 outline-none focus:border-[var(--accent)]" minLength={mode === "register" ? 12 : undefined} name="password" type="password" required />
      </label>
      {error && <p className="border-l-4 border-red-600 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      <button className="w-full bg-[var(--forest)] px-5 py-3.5 font-bold text-white disabled:opacity-60" disabled={pending}>
        {pending ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
      </button>
    </form>
  );
}

