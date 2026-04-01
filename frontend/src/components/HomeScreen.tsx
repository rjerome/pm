"use client";

import { FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { AUTH_STORAGE_KEY, login, verifyToken } from "@/lib/auth";

type AuthState = "checking" | "signed_out" | "signed_in";

const saveToken = (token: string) => {
  window.localStorage.setItem(AUTH_STORAGE_KEY, token);
};

const clearToken = () => {
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
};

export const HomeScreen = () => {
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const restoreSession = async () => {
      const token = window.localStorage.getItem(AUTH_STORAGE_KEY);

      if (!token) {
        setAuthState("signed_out");
        return;
      }

      try {
        await verifyToken(token);
        setAuthState("signed_in");
      } catch {
        clearToken();
        setAuthState("signed_out");
      }
    };

    void restoreSession();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!username.trim() || !password.trim()) {
      setErrorMessage("Enter both username and password.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const result = await login(username.trim(), password.trim());
      saveToken(result.token);
      setPassword("");
      setAuthState("signed_in");
    } catch {
      clearToken();
      setErrorMessage("Invalid credentials.");
      setAuthState("signed_out");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    setPassword("");
    setErrorMessage("");
    setAuthState("signed_out");
  };

  if (authState === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <div className="rounded-[28px] border border-[var(--stroke)] bg-white/85 px-8 py-6 text-center shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Session Check
          </p>
          <p className="mt-3 text-sm text-[var(--navy-dark)]">
            Confirming access to your workspace.
          </p>
        </div>
      </div>
    );
  }

  if (authState === "signed_in") {
    return <KanbanBoard onLogout={handleLogout} />;
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1120px] items-center px-6 py-12">
        <section className="grid w-full gap-8 rounded-[32px] border border-[var(--stroke)] bg-white/88 p-8 shadow-[var(--shadow)] backdrop-blur md:grid-cols-[1.1fr_0.9fr] md:p-10">
          <div className="flex flex-col justify-between gap-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Project Management MVP
              </p>
              <h1 className="mt-4 font-display text-4xl font-semibold text-[var(--navy-dark)] md:text-5xl">
                Sign in to open your Kanban workspace.
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--gray-text)]">
                This MVP uses one demo account backed by the FastAPI backend.
                Once signed in, your board opens locally with the current single-board flow.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-3xl border border-[var(--stroke)] bg-[var(--surface)] p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Username
                </p>
                <p className="mt-3 text-2xl font-semibold text-[var(--primary-blue)]">
                  user
                </p>
              </div>
              <div className="rounded-3xl border border-[var(--stroke)] bg-[var(--surface)] p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Password
                </p>
                <p className="mt-3 text-2xl font-semibold text-[var(--secondary-purple)]">
                  password
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[28px] border border-[var(--stroke)] bg-[var(--surface)] p-6 md:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
              Access
            </p>
            <h2 className="mt-3 font-display text-2xl font-semibold text-[var(--navy-dark)]">
              Welcome back
            </h2>
            <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                  Username
                </span>
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  className="mt-2 w-full rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                />
              </label>
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                  Password
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  className="mt-2 w-full rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                />
              </label>

              {errorMessage ? (
                <p
                  role="alert"
                  className="rounded-2xl border border-[rgba(117,57,145,0.16)] bg-[rgba(117,57,145,0.08)] px-4 py-3 text-sm text-[var(--secondary-purple)]"
                >
                  {errorMessage}
                </p>
              ) : null}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isSubmitting ? "Signing in..." : "Sign in"}
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
};
