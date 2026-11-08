"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  FileText,
  BadgeCheck,
  SpellCheck,
  UserCheck,
  Sliders,
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  Clock,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { StatCard } from "@/components/shared/stat-card";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { api } from "@/lib/api";
import { KnowledgeOverviewStats } from "@/types/brand";

export default function BrandKnowledgeHubPage() {
  const [stats, setStats] = useState<KnowledgeOverviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        setLoading(true);
        const res = await api.brand.getOverview();
        if (res.success && res.data) {
          setStats(res.data);
        } else {
          setError(res.error?.message || "Failed to load knowledge metrics");
        }
      } catch (err: any) {
        setError(err.message || "Failed to communicate with server");
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  return (
    <div>
      <Header
        title="Brand Knowledge Hub"
        description="Single source of truth for guidelines, product specifications, claims, and terminology rules."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Core Governance Principle Alert Banner */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-orange-50 via-amber-50 to-orange-50 border border-orange-200/80 flex items-start gap-3 shadow-xs">
          <ShieldCheck className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-slate-900">
              Active Knowledge Policy: Explicit Human Approval Required
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Only verified and explicitly approved documents, facts, and terminology rules become active organisational knowledge.
              Uploaded files and proposed facts remain pending and isolated from content review until approved by a Brand Manager or Admin.
            </p>
          </div>
        </div>

        {/* Overview Stats */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
            {error}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <StatCard
              title="Brand Documents"
              value={stats?.total_documents ?? 0}
              subtext={`${stats?.approved_documents ?? 0} approved • ${stats?.pending_documents ?? 0} pending`}
              icon={FileText}
            />
            <StatCard
              title="Approved Facts & Claims"
              value={stats?.approved_facts ?? 0}
              subtext={`${stats?.pending_facts ?? 0} pending review`}
              icon={BadgeCheck}
            />
            <StatCard
              title="Active Terminology Rules"
              value={stats?.active_terminology_rules ?? 0}
              subtext={`${stats?.total_terminology_rules ?? 0} total rules configured`}
              icon={SpellCheck}
            />
            <StatCard
              title="Extracted Knowledge Chunks"
              value={stats?.total_chunks ?? 0}
              subtext="Searchable, page-referenced text segments"
              icon={Layers}
            />
          </div>
        )}

        {/* Modules Grid */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
            Knowledge Hub Modules
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Brand Profile */}
            <Link
              href="/brand-knowledge/profile"
              className="group p-6 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-orange-100/80 text-brand-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <Sliders className="w-5 h-5" />
                </div>
                <h4 className="text-base font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                  Brand Profile & Voice
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Define your brand identity, tone of voice, target audiences, publishing channels, and regional applicability.
                </p>
              </div>
              <div className="mt-5 flex items-center gap-1.5 text-xs font-semibold text-brand-600">
                <span>Manage Profile</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Documents */}
            <Link
              href="/brand-knowledge/documents"
              className="group p-6 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100/80 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <FileText className="w-5 h-5" />
                </div>
                <h4 className="text-base font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                  Guidelines & Reference Docs
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Upload DOCX and text-based PDFs. Automatic text normalization, page-number preservation, and chunking.
                </p>
              </div>
              <div className="mt-5 flex items-center gap-1.5 text-xs font-semibold text-brand-600">
                <span>Browse Documents</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Facts */}
            <Link
              href="/brand-knowledge/facts"
              className="group p-6 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-100/80 text-emerald-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <BadgeCheck className="w-5 h-5" />
                </div>
                <h4 className="text-base font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                  Approved Facts & Claims
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Maintain verified product specifications, certifications, and compliance claims backed by document evidence.
                </p>
              </div>
              <div className="mt-5 flex items-center gap-1.5 text-xs font-semibold text-brand-600">
                <span>View Facts</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Terminology */}
            <Link
              href="/brand-knowledge/terminology"
              className="group p-6 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100/80 text-purple-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <SpellCheck className="w-5 h-5" />
                </div>
                <h4 className="text-base font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                  Terminology Rules & Linter
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Configure preferred vs prohibited terms with exact, whole-word, or phrase matching. Test text interactively.
                </p>
              </div>
              <div className="mt-5 flex items-center gap-1.5 text-xs font-semibold text-brand-600">
                <span>Manage Terminology</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Approvals */}
            <Link
              href="/brand-knowledge/approvals"
              className="group p-6 rounded-xl border border-slate-200 bg-white hover:border-brand-500 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-amber-100/80 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <UserCheck className="w-5 h-5" />
                </div>
                <h4 className="text-base font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                  Knowledge Approval History
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Full audit log of human approval, rejection, and archival decisions across documents, facts, and terms.
                </p>
              </div>
              <div className="mt-5 flex items-center gap-1.5 text-xs font-semibold text-brand-600">
                <span>Review Audit Trail</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
