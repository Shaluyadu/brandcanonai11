"use client";

import React from "react";
import { User, Shield, KeyRound, Mail, Building2, LogOut, CheckCircle2, AlertCircle } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/layout/header";
import { formatDate } from "@/lib/utils";

export default function UserSettingsPage() {
  const { user, activeOrganisation, currentRole, logout } = useAuth();

  return (
    <div>
      <Header
        title="Account & Security Settings"
        description="User profile details, authentication credentials, and active session management."
      />

      <div className="p-8 max-w-4xl mx-auto space-y-6">
        {/* User Identity Card */}
        <div className="p-6 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
            <User className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-bold text-slate-900">User Profile</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-500 mb-1">Full Name</label>
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-medium">
                {user?.full_name || "—"}
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-500 mb-1">Email Address</label>
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-medium flex items-center justify-between">
                <span>{user?.email || "—"}</span>
                {user?.is_verified ? (
                  <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3" />
                    Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    <AlertCircle className="w-3 h-3" />
                    Verification Unconfigured
                  </span>
                )}
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-500 mb-1">Active Workspace</label>
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-medium">
                {activeOrganisation?.name || "—"}
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-500 mb-1">Assigned Role</label>
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-medium">
                {currentRole?.replace("_", " ") || "—"}
              </div>
            </div>
          </div>
        </div>

        {/* Security & Authentication Protocol */}
        <div className="p-6 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
            <Shield className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-bold text-slate-900">Security Architecture</h3>
          </div>

          <div className="space-y-3 text-xs text-slate-600">
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
              <KeyRound className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-900">Argon2id Password Protection:</span> Passwords are saved using memory-hard Argon2id hashing algorithms with dynamic salt. Plaintext passwords are never logged or stored.
              </div>
            </div>

            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
              <Shield className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-900">Opaque Database Sessions:</span> Browser sessions are authenticated with cryptographically randomized 256-bit opaque tokens hashed (SHA-256) inside the database. Logging out immediately revokes session validity.
              </div>
            </div>
          </div>
        </div>

        {/* Session Termination */}
        <div className="p-6 rounded-xl border border-rose-200 bg-white shadow-xs flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Sign Out of Workspace</h4>
            <p className="text-xs text-slate-500">
              Revokes the active database session and clears all browser credentials.
            </p>
          </div>
          <button
            onClick={logout}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
}

