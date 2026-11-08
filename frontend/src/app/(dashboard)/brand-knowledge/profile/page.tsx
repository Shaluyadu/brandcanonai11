"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Save, Sliders, CheckCircle2, AlertCircle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { BrandProfile } from "@/types/brand";

export default function BrandProfilePage() {
  const { currentRole } = useAuth();
  const canEdit = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [hasExisting, setHasExisting] = useState(false);
  const [formData, setFormData] = useState({
    brand_name: "",
    industry: "",
    domain: "",
    description: "",
    brand_voice: "",
    target_audience: "",
    publishing_channels: "Website, LinkedIn, Press Releases, Blog",
    applicable_regions: "Global, North America, Europe",
  });

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        const res = await api.brand.getProfile();
        if (res.success && res.data) {
          const p = res.data;
          setHasExisting(true);
          setFormData({
            brand_name: p.brand_name || "",
            industry: p.industry || "",
            domain: p.domain || "",
            description: p.description || "",
            brand_voice: p.brand_voice || "",
            target_audience: p.target_audience || "",
            publishing_channels: (p.publishing_channels || []).join(", "),
            applicable_regions: (p.applicable_regions || []).join(", "),
          });
        }
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to load brand profile");
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;

    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    const payload: Partial<BrandProfile> = {
      brand_name: formData.brand_name.trim(),
      industry: formData.industry.trim() || undefined,
      domain: formData.domain.trim() || undefined,
      description: formData.description.trim() || undefined,
      brand_voice: formData.brand_voice.trim() || undefined,
      target_audience: formData.target_audience.trim() || undefined,
      publishing_channels: formData.publishing_channels
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      applicable_regions: formData.applicable_regions
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };

    try {
      const res = hasExisting
        ? await api.brand.updateProfile(payload)
        : await api.brand.createProfile(payload);

      if (res.success) {
        setHasExisting(true);
        setSuccessMsg("Brand profile saved successfully!");
      } else {
        setErrorMsg(res.error?.message || "Failed to save brand profile");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Network error while saving profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Header
        title="Brand Profile & Voice"
        description="Establish the core identity, voice, tone, and audience targeting rules for your organisation."
      />

      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <Link
          href="/brand-knowledge"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Knowledge Hub</span>
        </Link>

        {successMsg && (
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {!canEdit && (
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
            Viewing in read-only mode. Only Admins and Brand Managers can modify the brand profile.
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Brand Name *
              </label>
              <input
                type="text"
                required
                disabled={!canEdit || loading}
                value={formData.brand_name}
                onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                placeholder="e.g. Acme Corporation"
                className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Industry
              </label>
              <input
                type="text"
                disabled={!canEdit || loading}
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                placeholder="e.g. Enterprise Cloud Software"
                className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Primary Domain
              </label>
              <input
                type="text"
                disabled={!canEdit || loading}
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                placeholder="e.g. acme.com"
                className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Publishing Channels (comma separated)
              </label>
              <input
                type="text"
                disabled={!canEdit || loading}
                value={formData.publishing_channels}
                onChange={(e) => setFormData({ ...formData, publishing_channels: e.target.value })}
                placeholder="e.g. Website, LinkedIn, Press Releases, Blog"
                className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Brand Voice & Tone Principles
            </label>
            <textarea
              rows={4}
              disabled={!canEdit || loading}
              value={formData.brand_voice}
              onChange={(e) => setFormData({ ...formData, brand_voice: e.target.value })}
              placeholder="Describe your brand voice principles (e.g. Authoritative yet approachable, concise, factual, avoiding hype or exaggerated superlatives)."
              className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Target Audience
            </label>
            <textarea
              rows={3}
              disabled={!canEdit || loading}
              value={formData.target_audience}
              onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
              placeholder="Describe key buyer personas and audience profiles (e.g. Chief Marketing Officers, Enterprise Compliance Officers, Legal Teams)."
              className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Applicable Regions (comma separated)
            </label>
            <input
              type="text"
              disabled={!canEdit || loading}
              value={formData.applicable_regions}
              onChange={(e) => setFormData({ ...formData, applicable_regions: e.target.value })}
              placeholder="e.g. Global, North America, Europe, Asia Pacific"
              className="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:bg-slate-50"
            />
          </div>

          {canEdit && (
            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                disabled={saving || loading}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm transition-colors shadow-sm disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? "Saving..." : "Save Brand Profile"}</span>
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

