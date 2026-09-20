import Link from "next/link";

import { AuthForm } from "./auth-form";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const isLogin = mode === "login";
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <section className="flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-md">
          <Link className="text-lg font-black tracking-tight" href="/">LOCUS / AI</Link>
          <p className="mt-14 text-xs font-bold uppercase tracking-[0.22em] text-[var(--accent)]">{isLogin ? "Welcome back" : "Start your archive"}</p>
          <h1 className="mt-4 text-5xl font-black tracking-[-0.05em]">{isLogin ? "Log in" : "Create account"}</h1>
          <AuthForm mode={mode} />
          <p className="mt-6 text-sm text-black/60">
            {isLogin ? "New to Locus?" : "Already have an account?"}{" "}
            <Link className="font-bold text-[var(--forest)] underline" href={isLogin ? "/register" : "/login"}>
              {isLogin ? "Create an account" : "Log in"}
            </Link>
          </p>
        </div>
      </section>
      <aside className="hidden bg-[var(--forest)] p-16 text-white lg:flex lg:flex-col lg:justify-end">
        <p className="max-w-xl text-5xl font-black leading-tight tracking-[-0.04em]">Your documents remain yours. Every answer remains inspectable.</p>
        <p className="mt-8 max-w-lg text-lg leading-8 text-white/65">Strong password hashing, bearer authentication, and ownership checks protect every document and query.</p>
      </aside>
    </main>
  );
}

