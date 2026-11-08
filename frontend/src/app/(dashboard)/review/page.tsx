"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Sparkles,
  ShieldCheck,
  FileSearch,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Check,
  X,
  FileText,
  Clock,
  Layers,
  BookOpen,
  MessageSquare,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { SubmissionDetail, FindingDetail } from "@/types/submission";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";

function ReviewStudioContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const submissionId = searchParams.get("id");
  const { currentRole, isReviewer, isAdmin, isBrandManager } = useAuth();

  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFindingId, setActiveFindingId] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number>(1);
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [actionLoading, setActionLoading] = useState(false);

  // Decision Modal
  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [decisionType, setDecisionType] = useState<"APPROVED" | "REQUEST_CHANGES" | "CHANGES_REQUESTED" | "REJECTED">("APPROVED");
  const [decisionNotes, setDecisionNotes] = useState("");

  const fetchDetail = useCallback(async (id: string) => {
    setLoading(true);
    try {
      const res = await api.governance.getSubmission(id);
      if (res.success && res.data) {
        setSubmission(res.data);
        setSelectedVersion(res.data.current_version_number);
      }
    } catch (err) {
      console.error("Failed to load submission", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (submissionId) {
      fetchDetail(submissionId);
    } else {
      setLoading(false);
    }
  }, [submissionId, fetchDetail]);

  const handleApplySuggestion = async (suggestionId: string) => {
    if (!submission) return;
    setActionLoading(true);
    try {
      const res = await api.governance.handleSuggestionAction(suggestionId, "APPLY");
      if (res.success) {
        await fetchDetail(submission.id);
      }
    } catch (err) {
      console.error("Failed to apply suggestion", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectSuggestion = async (suggestionId: string) => {
    if (!submission) return;
    setActionLoading(true);
    try {
      const res = await api.governance.handleSuggestionAction(suggestionId, "REJECT");
      if (res.success) {
        await fetchDetail(submission.id);
      }
    } catch (err) {
      console.error("Failed to reject suggestion", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitDecision = async () => {
    if (!submission) return;
    setActionLoading(true);
    try {
      const res = await api.governance.decideSubmission(submission.id, {
        decision: decisionType,
        notes: decisionNotes.trim() || undefined,
      });
      if (res.success && res.data) {
        setSubmission(res.data);
        setDecisionModalOpen(false);
        setDecisionNotes("");
      }
    } catch (err) {
      console.error("Failed to record decision", err);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-4">
        <div className="h-8 bg-slate-200 rounded w-1/3 animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 bg-white rounded-xl border border-slate-200 animate-pulse" />
          <div className="h-96 bg-white rounded-xl border border-slate-200 animate-pulse" />
        </div>
      </div>
    );
  }

  if (!submissionId || !submission) {
    return (
      <div>
        <Header
          title="AI Review Studio"
          description="Split-screen evidence-grounded review interface with inline highlights, findings, and suggestions."
        />
        <div className="p-8 max-w-7xl mx-auto space-y-6">
          <EmptyState
            icon={FileSearch}
            title="No Submission Selected"
            description="Select an active content submission from your queue to inspect AI findings and suggestions."
            actionText="Go to Content Submissions"
            actionHref="/submissions"
          />
        </div>
      </div>
    );
  }

  const currentVersionData =
    submission.versions.find((v) => v.version_number === selectedVersion) ||
    submission.versions[0];

  const findings = submission.latest_review_result?.findings || [];
  const filteredFindings = findings.filter(
    (f) => categoryFilter === "ALL" || f.category === categoryFilter
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "CHANGES_REQUESTED":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "REJECTED":
        return "bg-rose-50 text-rose-700 border-rose-200";
      default:
        return "bg-blue-50 text-blue-700 border-blue-200";
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Header / Bar */}
      <div className="border-b border-slate-200 bg-white px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/submissions"
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">{submission.title}</h2>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadge(
                  submission.current_status
                )}`}
              >
                {submission.current_status.replace("_", " ")}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500 pt-0.5">
              <span>Channel: <strong className="text-slate-700">{submission.publishing_channel}</strong></span>
              <span>•</span>
              <span>Audience: <strong className="text-slate-700">{submission.target_audience || "General"}</strong></span>
              <span>•</span>
              <span>Updated: {formatDate(submission.updated_at)}</span>
            </div>
          </div>
        </div>

        {/* Governance Decision Controls */}
        {(isReviewer || isAdmin || isBrandManager) && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setDecisionType("CHANGES_REQUESTED");
                setDecisionModalOpen(true);
              }}
              className="px-3 py-1.5 rounded-lg border border-amber-200 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition-colors"
            >
              Request Changes
            </button>
            <button
              onClick={() => {
                setDecisionType("REJECTED");
                setDecisionModalOpen(true);
              }}
              className="px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-800 text-xs font-semibold transition-colors"
            >
              Reject
            </button>
            <button
              onClick={() => {
                setDecisionType("APPROVED");
                setDecisionModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Approve Draft</span>
            </button>
          </div>
        )}
      </div>

      {/* Split-Screen Review Canvas */}
      <div className="px-8 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 pb-12">
        {/* Left Side: Content Viewer (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col h-[750px]">
          {/* Version Switcher Header */}
          <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/60 rounded-t-xl text-xs">
            <div className="flex items-center gap-2 text-slate-700 font-semibold">
              <Layers className="w-4 h-4 text-brand-600" />
              <span>Version History</span>
              <select
                value={selectedVersion}
                onChange={(e) => setSelectedVersion(Number(e.target.value))}
                className="px-2 py-1 bg-white border border-slate-200 rounded text-xs font-medium"
              >
                {submission.versions.map((v) => (
                  <option key={v.id} value={v.version_number}>
                    v{v.version_number} ({formatDate(v.created_at)})
                  </option>
                ))}
              </select>
            </div>
            <div className="text-slate-500">
              {currentVersionData?.word_count || 0} words • {currentVersionData?.character_count || 0} characters
            </div>
          </div>

          {/* Content Document Display with Highlight Navigation */}
          <div className="p-6 overflow-y-auto flex-1 font-serif text-slate-800 leading-relaxed text-sm whitespace-pre-wrap select-text">
            {currentVersionData?.content_text}
          </div>

          {/* Footer Metadata */}
          <div className="px-5 py-2.5 border-t border-slate-100 bg-slate-50/40 rounded-b-xl text-[11px] text-slate-400 flex items-center justify-between">
            <span>SHA-256: {currentVersionData?.content_hash?.substring(0, 16)}...</span>
            <span>Deterministic Grounding Active</span>
          </div>
        </div>

        {/* Right Side: AI Findings, Grounded Evidence & Suggestions (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col h-[750px]">
          {/* Header & Category Filter Tabs */}
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60 rounded-t-xl space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-600" />
                <h3 className="text-xs font-bold text-slate-900">
                  Compliance Findings ({findings.length})
                </h3>
              </div>
              <span className="text-[11px] text-slate-500">
                {findings.length === 0 ? "All checks passed" : `${findings.length} issue(s) detected`}
              </span>
            </div>

            <div className="flex items-center gap-1.5 pt-1">
              {["ALL", "TERMINOLOGY", "CLAIM"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors ${
                    categoryFilter === cat
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Findings List */}
          <div className="p-4 overflow-y-auto flex-1 space-y-4">
            {filteredFindings.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
                <CheckCircle className="w-10 h-10 text-emerald-500 mb-2" />
                <h4 className="text-xs font-bold text-slate-700">No Violations Found</h4>
                <p className="text-[11px] text-slate-400 max-w-xs mt-1">
                  This content version satisfies all active terminology standards and verified brand claims.
                </p>
              </div>
            ) : (
              filteredFindings.map((finding) => (
                <div
                  key={finding.id}
                  onClick={() => setActiveFindingId(finding.id)}
                  className={`p-4 rounded-xl border text-xs transition-all space-y-3 ${
                    activeFindingId === finding.id
                      ? "border-brand-500 bg-brand-50/20 shadow-xs ring-1 ring-brand-500"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  {/* Category & Severity Badges */}
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-700 font-semibold">
                      {finding.category}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        finding.severity === "CRITICAL" || finding.severity === "HIGH"
                          ? "bg-rose-100 text-rose-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {finding.severity}
                    </span>
                  </div>

                  {/* Flagged Text */}
                  <div className="p-2 bg-slate-50 rounded-lg border border-slate-100 font-mono text-[11px] text-slate-800">
                    &ldquo;{finding.original_text}&rdquo;
                  </div>

                  {/* Explanation */}
                  <p className="text-slate-600 text-xs leading-relaxed">
                    {finding.explanation}
                  </p>

                  {/* Grounded Evidence Citation if present */}
                  {finding.evidences.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-orange-50/60 border border-orange-200 space-y-1">
                      <div className="flex items-center gap-1.5 text-[10px] font-bold text-orange-900">
                        <BookOpen className="w-3 h-3 text-orange-600" />
                        <span>Grounded Source Evidence</span>
                      </div>
                      <p className="text-[11px] text-orange-950 italic">
                        &ldquo;{finding.evidences[0].source_quote}&rdquo;
                      </p>
                    </div>
                  )}

                  {/* Suggestion Workspace */}
                  {finding.suggestion && (
                    <div className="p-3 bg-brand-50/60 rounded-xl border border-brand-200 space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-brand-900">AI Suggested Revision:</span>
                        <span className="font-mono text-[10px] text-brand-700">{finding.suggestion.status}</span>
                      </div>
                      <div className="font-mono text-xs font-semibold text-brand-700">
                        &ldquo;{finding.suggestion.suggested_text}&rdquo;
                      </div>
                      {finding.suggestion.status === "PENDING" && (
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            disabled={actionLoading}
                            onClick={() => handleApplySuggestion(finding.suggestion!.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-[11px] font-semibold transition-colors disabled:opacity-50"
                          >
                            <Check className="w-3 h-3" />
                            <span>Apply Suggestion</span>
                          </button>
                          <button
                            disabled={actionLoading}
                            onClick={() => handleRejectSuggestion(finding.suggestion!.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-[11px] font-semibold transition-colors disabled:opacity-50"
                          >
                            <X className="w-3 h-3" />
                            <span>Dismiss</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Decision Modal */}
      {decisionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900">
                Confirm Decision: {decisionType.replace("_", " ")}
              </h3>
              <button
                onClick={() => setDecisionModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Please enter formal reviewer notes or feedback to accompany this governance decision.
            </p>

            <textarea
              rows={3}
              value={decisionNotes}
              onChange={(e) => setDecisionNotes(e.target.value)}
              placeholder="e.g. Reviewed and approved for publication across digital channels."
              className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setDecisionModalOpen(false)}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                disabled={actionLoading}
                onClick={handleSubmitDecision}
                className="px-4 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
              >
                {actionLoading ? "Recording..." : "Confirm Decision"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReviewStudioPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-400">Loading Review Studio...</div>}>
      <ReviewStudioContent />
    </Suspense>
  );
}
