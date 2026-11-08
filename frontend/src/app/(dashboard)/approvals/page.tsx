"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ShieldCheck,
  UserCheck,
  ArrowRight,
  Clock,
  Sparkles,
  Check,
  X,
  FileSearch,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { SubmissionListItem } from "@/types/submission";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";

export default function ApprovalsPage() {
  const { isReviewer, isAdmin, isBrandManager, activeOrganisation } = useAuth();
  const [pendingSubmissions, setPendingSubmissions] = useState<SubmissionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchPending = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.governance.getSubmissions({
        status: "SUBMITTED",
        pageSize: 50,
      });
      if (res.success && res.data) {
        setPendingSubmissions(res.data.items);
      }
    } catch (err) {
      console.error("Failed to load approval queue", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  const handleQuickApprove = async (id: string) => {
    setActionLoading(id);
    try {
      const res = await api.governance.decideSubmission(id, {
        decision: "APPROVED",
        notes: "Quick approval by authorized reviewer.",
      });
      if (res.success) {
        fetchPending();
      }
    } catch (err) {
      console.error("Failed to approve", err);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div>
      <Header
        title="Approval Workspace"
        description="Formal human-in-the-loop review queue for authorized decision-makers."
      />
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="p-5 rounded-xl bg-emerald-50/60 border border-emerald-200 text-xs text-emerald-800 flex items-start gap-3">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Human Governance Lifecycle (Phase 5):</span> Authorized Reviewers inspect revisions, evaluate AI-detected evidence, and record formal decisions. Automated algorithms flag violations, but authorized humans retain final publication authority.
          </div>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-white rounded-xl border border-slate-200 animate-pulse" />
            ))}
          </div>
        ) : pendingSubmissions.length === 0 ? (
          <EmptyState
            icon={CheckCircle2}
            title="Approval Queue is Clear"
            description="There are currently no content submissions awaiting your review or decision."
            actionText="Workspace Overview"
            actionHref="/dashboard"
          />
        ) : (
          <div className="space-y-4">
            <div className="text-xs font-semibold text-slate-500">
              {pendingSubmissions.length} submission(s) awaiting governance evaluation
            </div>
            <div className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
              {pendingSubmissions.map((sub) => (
                <div
                  key={sub.id}
                  className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-900">{sub.title}</h4>
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                        {sub.publishing_channel}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-3">
                      <span>Audience: <strong>{sub.target_audience || "General"}</strong></span>
                      <span>•</span>
                      <span>Submitted: {formatDate(sub.created_at)}</span>
                      <span>•</span>
                      <span>Review: <strong>{sub.latest_review_status || "Pending"}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Link
                      href={`/review?id=${sub.id}`}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-xs transition-colors"
                    >
                      <FileSearch className="w-3.5 h-3.5" />
                      <span>Open Review Studio</span>
                    </Link>

                    {(isReviewer || isAdmin || isBrandManager) && (
                      <button
                        disabled={actionLoading === sub.id}
                        onClick={() => handleQuickApprove(sub.id)}
                        className="inline-flex items-center gap-1 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{actionLoading === sub.id ? "Approving..." : "Approve"}</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
