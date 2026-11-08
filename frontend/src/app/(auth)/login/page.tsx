"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, ArrowRight, AlertCircle, Sparkles, UserCheck } from "lucide-react";
import { useAuth } from "@/context/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage("Please enter both email and password");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const res = await login(email, password);
    setIsSubmitting(false);

    if (res.success) {
      router.push("/dashboard");
    } else {
      setErrorMessage(res.error || "Invalid credentials");
    }
  };

  const fillDemoAccount = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("NovaTech@2026!");
    setErrorMessage(null);
  };

  const showDemoAccounts =
    process.env.NODE_ENV !== "production" ||
    process.env.NEXT_PUBLIC_ENABLE_DEMO_LOGINS === "true";

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-slate-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-600 text-white shadow-md shadow-brand-500/30 mb-3">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Sign in to BrandCanon AI
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Enterprise Evidence-Grounded Brand Governance SaaS
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
          {errorMessage && (
            <div className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Work Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-colors"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700">Password</label>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold shadow-xs shadow-brand-600/30 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? "Signing in..." : "Sign In to Workspace"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Fictional Demo Accounts Quick Fill (Only visible in Development / Demo mode) */}
          {showDemoAccounts && (
            <div className="mt-6 pt-6 border-t border-slate-100">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                NovaTech Demo Workspace Logins
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => fillDemoAccount("admin@novatech.io")}
                  className="p-2 text-left rounded-lg border border-slate-200 bg-slate-50 hover:bg-brand-50/70 hover:border-brand-300 transition-all text-slate-700"
                >
                  <div className="font-semibold text-slate-900 text-[11px]">Workspace Admin</div>
                  <div className="text-[10px] text-slate-500 truncate">admin@novatech.io</div>
                </button>
                <button
                  type="button"
                  onClick={() => fillDemoAccount("brand@novatech.io")}
                  className="p-2 text-left rounded-lg border border-slate-200 bg-slate-50 hover:bg-brand-50/70 hover:border-brand-300 transition-all text-slate-700"
                >
                  <div className="font-semibold text-slate-900 text-[11px]">Brand Manager</div>
                  <div className="text-[10px] text-slate-500 truncate">brand@novatech.io</div>
                </button>
                <button
                  type="button"
                  onClick={() => fillDemoAccount("creator@novatech.io")}
                  className="p-2 text-left rounded-lg border border-slate-200 bg-slate-50 hover:bg-brand-50/70 hover:border-brand-300 transition-all text-slate-700"
                >
                  <div className="font-semibold text-slate-900 text-[11px]">Content Creator</div>
                  <div className="text-[10px] text-slate-500 truncate">creator@novatech.io</div>
                </button>
                <button
                  type="button"
                  onClick={() => fillDemoAccount("reviewer@novatech.io")}
                  className="p-2 text-left rounded-lg border border-slate-200 bg-slate-50 hover:bg-brand-50/70 hover:border-brand-300 transition-all text-slate-700"
                >
                  <div className="font-semibold text-slate-900 text-[11px]">Reviewer / Legal</div>
                  <div className="text-[10px] text-slate-500 truncate">reviewer@novatech.io</div>
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 text-center text-xs text-slate-500">
            Need an organization workspace?{" "}
            <Link href="/signup" className="font-semibold text-brand-600 hover:text-brand-700">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

