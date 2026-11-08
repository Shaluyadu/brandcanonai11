"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BadgeCheck,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  Archive,
  Trash2,
  Filter,
  ArrowLeft,
  Quote,
  ShieldCheck,
  Tag,
  AlertCircle
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { ApprovedFact } from "@/types/brand";

const CATEGORIES = [
  "PRODUCT_SPECIFICATION",
  "COMPLIANCE",
  "PRICING",
  "PERFORMANCE",
  "CERTIFICATION",
  "SECURITY",
  "COMPANY_HISTORY",
];

export default function ApprovedFactsPage() {
  const { currentRole } = useAuth();
  const canCreate = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER" || currentRole === "CREATOR";
  const canApprove = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER";

  const [facts, setFacts] = useState<ApprovedFact[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    title: "",
    claim_text: "",
    category: "PRODUCT_SPECIFICATION",
    evidence_quote: "",
    source_page: "",
    source_location: "",
    applicable_region: "GLOBAL",
    applicable_audience: "ALL",
  });

  const fetchFacts = async () => {
    try {
      setLoading(true);
      const res = await api.brand.listFacts({
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
      });
      if (res.success && res.data) {
        setFacts(res.data.items);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFacts();
  }, [statusFilter, categoryFilter]);

  const handleCreateFact = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const payload: Partial<ApprovedFact> = {
      title: formData.title.trim(),
      claim_text: formData.claim_text.trim(),
      category: formData.category,
      evidence_quote: formData.evidence_quote.trim() || undefined,
      source_page: formData.source_page ? parseInt(formData.source_page, 10) : undefined,
      source_location: formData.source_location.trim() || undefined,
      applicable_region: formData.applicable_region.trim(),
      applicable_audience: formData.applicable_audience.trim(),
    };

    try {
      const res = await api.brand.createFact(payload);
      if (res.success) {
        setShowModal(false);
        setFormData({
          title: "",
          claim_text: "",
          category: "PRODUCT_SPECIFICATION",
          evidence_quote: "",
          source_page: "",
          source_location: "",
          applicable_region: "GLOBAL",
          applicable_audience: "ALL",
        });
        fetchFacts();
      } else {
        setErrorMsg(res.error?.message || "Failed to create fact");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit fact");
    }
  };

  const handleApprove = async (id: string) => {
    const reason = prompt("Enter approval remarks (optional):") || undefined;
    const res = await api.brand.approveFact(id, reason);
    if (res.success) fetchFacts();
  };

  const handleReject = async (id: string) => {
    const reason = prompt("Enter rejection reason:") || undefined;
    const res = await api.brand.rejectFact(id, reason);
    if (res.success) fetchFacts();
  };

  const handleArchive = async (id: string) => {
    const reason = prompt("Enter archive remarks:") || undefined;
    const res = await api.brand.archiveFact(id, reason);
    if (res.success) fetchFacts();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this approved fact?")) return;
    const res = await api.brand.deleteFact(id);
    if (res.success) fetchFacts();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200"><CheckCircle2 className="w-3 h-3 text-emerald-600" /> Approved</span>;
      case "PENDING_APPROVAL":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200"><Clock className="w-3 h-3 text-amber-600" /> Pending Approval</span>;
      case "REJECTED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200"><XCircle className="w-3 h-3 text-rose-600" /> Rejected</span>;
      case "ARCHIVED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200"><Archive className="w-3 h-3 text-slate-500" /> Archived</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">{status}</span>;
    }
  };

  return (
    <div>
      <Header
        title="Approved Facts & Claims"
        description="Verified specifications, certifications, and factual statements for grounding AI and human content."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Top Actions & Filters */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">All Statuses</option>
              <option value="APPROVED">Approved (Active Knowledge)</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="REJECTED">Rejected</option>
              <option value="ARCHIVED">Archived</option>
            </select>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>

          {canCreate && (
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Submit New Fact</span>
            </button>
          )}
        </div>

        {/* Facts List */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </div>
        ) : facts.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-12">
            <EmptyState
              icon={BadgeCheck}
              title="No Facts Found"
              description="Submit verified product specifications, benchmark numbers, or compliance claims."
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {facts.map((fact) => (
              <div
                key={fact.id}
                className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-slate-300 transition-colors"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      {fact.category.replace("_", " ")}
                    </span>
                    {getStatusBadge(fact.status)}
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 leading-snug">{fact.title}</h4>
                  <p className="text-xs text-slate-700 leading-relaxed">{fact.claim_text}</p>

                  {fact.evidence_quote && (
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-2 text-xs text-slate-600 italic">
                      <Quote className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <span>&ldquo;{fact.evidence_quote}&rdquo;</span>
                    </div>
                  )}

                  {(fact.source_page || fact.source_location) && (
                    <div className="text-[11px] text-slate-400">
                      Source: {fact.source_page && `Page ${fact.source_page}`} {fact.source_location && `• ${fact.source_location}`}
                    </div>
                  )}
                </div>

                {/* Footer Controls */}
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-400 text-[11px]">Region: {fact.applicable_region}</span>
                  <div className="flex items-center gap-1.5">
                    {canApprove && fact.status === "PENDING_APPROVAL" && (
                      <>
                        <button
                          onClick={() => handleApprove(fact.id)}
                          className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleReject(fact.id)}
                          className="px-2.5 py-1 text-xs font-semibold rounded bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors"
                        >
                          Reject
                        </button>
                      </>
                    )}

                    {canApprove && fact.status === "APPROVED" && (
                      <button
                        onClick={() => handleArchive(fact.id)}
                        className="px-2 py-1 text-xs text-slate-500 hover:text-slate-800 transition-colors"
                      >
                        Archive
                      </button>
                    )}

                    {canApprove && (
                      <button
                        onClick={() => handleDelete(fact.id)}
                        className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal: Create Fact */}
        {showModal && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-bold text-slate-900">Submit Approved Fact or Claim</h3>
                <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                  ✕
                </button>
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <form onSubmit={handleCreateFact} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Title *</label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="e.g. 99.99% Uptime SLA Guarantee"
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Claim Text *</label>
                  <textarea
                    rows={3}
                    required
                    value={formData.claim_text}
                    onChange={(e) => setFormData({ ...formData, claim_text: e.target.value })}
                    placeholder="Exact verified specification or statement to enforce..."
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="w-full px-2.5 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c}>
                          {c.replace("_", " ")}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Source Page #</label>
                    <input
                      type="number"
                      value={formData.source_page}
                      onChange={(e) => setFormData({ ...formData, source_page: e.target.value })}
                      placeholder="e.g. 14"
                      className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Evidence Quote</label>
                  <input
                    type="text"
                    value={formData.evidence_quote}
                    onChange={(e) => setFormData({ ...formData, evidence_quote: e.target.value })}
                    placeholder="Quoted text from source specification or legal approval document..."
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs"
                  >
                    Submit for Approval
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

