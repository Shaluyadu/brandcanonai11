"use client";

import React, { useEffect, useState } from "react";
import {
  Building2,
  Sliders,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Save,
  Lock
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { OrganisationDetail } from "@/types/auth";

export default function WorkspaceSettingsPage() {
  const { activeOrganisation, isAdmin, isBrandManager, refreshMe } = useAuth();
  const [orgData, setOrgData] = useState<OrganisationDetail | null>(null);
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [domain, setDomain] = useState("");
  const [enforceVoice, setEnforceVoice] = useState(true);
  const [strictMode, setStrictMode] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const canEdit = isAdmin || isBrandManager;

  useEffect(() => {
    const fetchOrg = async () => {
      setIsLoading(true);
      try {
        const res = await api.organisations.getCurrent();
        if (res.success && res.data) {
          setOrgData(res.data);
          setName(res.data.name || "");
          setIndustry(res.data.industry || "");
          setDomain(res.data.domain || "");
          if (res.data.settings) {
            setEnforceVoice(res.data.settings.enforce_brand_voice);
            setStrictMode(res.data.settings.strict_mode);
          }
        }
      } catch {
        setErrorMessage("Failed to load workspace configuration");
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrg();
  }, [activeOrganisation]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;

    setIsSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    const [profileRes, settingsRes] = await Promise.all([
      api.organisations.updateCurrent({ name, industry, domain }),
      isAdmin ? api.organisations.updateSettings({ enforce_brand_voice: enforceVoice, strict_mode: strictMode }) : Promise.resolve({ success: true }),
    ]);

    setIsSaving(false);

    if (profileRes.success) {
      setSuccessMessage("Workspace settings updated successfully");
      await refreshMe();
    } else {
      setErrorMessage(profileRes.error?.message || "Failed to update settings");
    }
  };

  return (
    <div>
      <Header
        title="Workspace Configuration"
        description="Organization metadata, brand profile parameters, and governance enforcement rules."
      />

      <div className="p-8 max-w-4xl mx-auto space-y-6">
        {successMessage && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-2.5 text-xs text-emerald-800">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-2.5 text-xs text-rose-800">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSaveProfile} className="space-y-6">
          {/* Workspace Identity */}
          <div className="p-6 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4">
            <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
              <Building2 className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-bold text-slate-900">Organization Profile</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Organization Name</label>
                <input
                  type="text"
                  required
                  disabled={!canEdit}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Workspace Slug</label>
                <input
                  type="text"
                  disabled
                  value={orgData?.slug || ""}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-slate-50 text-slate-500 cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Industry / Sector</label>
                <input
                  type="text"
                  disabled={!canEdit}
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. Enterprise Cloud Computing"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Corporate Domain</label>
                <input
                  type="text"
                  disabled={!canEdit}
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="e.g. novatech.io"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>
            </div>
          </div>

          {/* Governance Rules Configuration */}
          <div className="p-6 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4">
            <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
              <Sliders className="w-5 h-5 text-brand-600" />
              <h3 className="text-base font-bold text-slate-900">Governance & Review Engine Settings</h3>
            </div>

            <div className="space-y-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  disabled={!isAdmin}
                  checked={enforceVoice}
                  onChange={(e) => setEnforceVoice(e.target.checked)}
                  className="mt-1 w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
                />
                <div>
                  <div className="text-xs font-semibold text-slate-900">Enforce Strict Brand Terminology</div>
                  <div className="text-xs text-slate-500">
                    Deterministic checks for exact prohibited terms, preferred replacements, and channel-specific rules.
                  </div>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  disabled={!isAdmin}
                  checked={strictMode}
                  onChange={(e) => setStrictMode(e.target.checked)}
                  className="mt-1 w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
                />
                <div>
                  <div className="text-xs font-semibold text-slate-900">Strict Claim Grounding Mode</div>
                  <div className="text-xs text-slate-500">
                    Flag any quantitative, promotional, or factual claim that lacks verified source document evidence.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {canEdit && (
            <div className="flex items-center justify-end">
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs shadow-brand-600/30 transition-colors disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? "Saving Configuration..." : "Save Workspace Configuration"}</span>
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

