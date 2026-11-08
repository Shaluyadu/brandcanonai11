"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle,
  Sparkles,
  Users,
  ArrowRight,
  History,
  BookOpen,
  FileSearch,
  XCircle,
  AlertCircle,
  TrendingUp,
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/layout/header";
import { StatCard } from "@/components/shared/stat-card";
import { api } from "@/lib/api";
import { AuditLog } from "@/types/audit";
import { DashboardStats } from "@/types/governance";
import { formatDate } from "@/lib/utils";

export default function DashboardOverviewPage() {
  const { user, activeOrganisation, currentRole, isAdmin, isBrandManager, isCreator, isReviewer } = useAuth();
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [memberCount, setMemberCount] = useState<number>(0);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [auditRes, membersRes, dashboardRes] = await Promise.all([
          api.audit.list({ page: 1, pageSize: 5 }),
          api.members.list(1, 1),
          api.governance.getDashboard(),
        ]);
        if (auditRes.success && auditRes.data) {
          setRecentLogs(auditRes.data.items);
        }
        if (membersRes.success && membersRes.data) {
          setMemberCount(membersRes.data.total);
        }
        if (dashboardRes.success && dashboardRes.data) {
          setStats(dashboardRes.data);
        }
      } catch (err) {
        console.error("Failed to load dashboard metrics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeOrganisation]);

  const getRoleGreeting = () => {
    if (isAdmin) {
      return {
        title: "Workspace Administration & Governance",
        desc: "You have full administrative authority over members, roles, workspace configuration, and audit trails.",
        actionLabel: "Manage Workspace Members",
        actionHref: "/members",
      };
    }
    if (isBrandManager) {
      return {
        title: "Brand Knowledge & Compliance Hub",
        desc: "Oversee brand guidelines, verified facts, terminology rules, and human knowledge approvals.",
        actionLabel: "Open Knowledge Hub",
        actionHref: "/brand-knowledge",
      };
    }
    if (isCreator) {
      return {
        title: "Content Creation & Pre-Publication Review",
        desc: "Submit marketing copy, articles, or product text to run automated AI compliance checks before publishing.",
        actionLabel: "New Content Review",
        actionHref: "/submissions",
      };
    }
    return {
      title: "Content Review & Verification Queue",
      desc: "Inspect submitted content, evaluate evidence-grounded AI findings, and record formal approval decisions.",
      actionLabel: "Review Queue",
      actionHref: "/approvals",
    };
  };

  const roleInfo = getRoleGreeting();

  return (
    <div>
      <Header
        title="Workspace Overview"
        description={`Real-time brand compliance overview for ${activeOrganisation?.name || "your organization"}`}
      />
      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Role-Aware Banner */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-brand-500/20 text-brand-300 text-xs font-semibold border border-brand-500/30">
              <ShieldCheck className="w-3.5 h-3.5" />
              Role: {currentRole?.replace("_", " ")}
            </div>
            <h2 className="text-xl font-bold tracking-tight">{roleInfo.title}</h2>
            <p className="text-xs text-slate-300 max-w-2xl">{roleInfo.desc}</p>
            <div className="pt-2">
              <Link
                href={roleInfo.actionHref}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-xs transition-colors shrink-0"
              >
                <span>{roleInfo.actionLabel}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>

        {/* Phase 5 Live Governance Metrics — All 8 Organization-Scoped Backend Counts */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Live Governance Metrics</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Submissions"
              value={loading ? "…" : stats?.total_submissions?.toString() ?? "0"}
              subtext="Org-scoped drafts & publications"
              icon={FileText}
              variant="default"
            />
            <StatCard
              title="Pending Reviews"
              value={loading ? "…" : stats?.pending_reviews?.toString() ?? "0"}
              subtext="Awaiting review completion"
              icon={Clock}
              variant="amber"
            />
            <StatCard
              title="In-Review Submissions"
              value={loading ? "…" : stats?.in_review?.toString() ?? "0"}
              subtext="Actively undergoing checks"
              icon={FileSearch}
              variant="default"
            />
            <StatCard
              title="Changes Requested"
              value={loading ? "…" : stats?.changes_requested?.toString() ?? "0"}
              subtext="Requires creator modifications"
              icon={AlertCircle}
              variant="amber"
            />
            <StatCard
              title="Approved Submissions"
              value={loading ? "…" : stats?.approved?.toString() ?? "0"}
              subtext="Human-authorized and compliant"
              icon={CheckCircle}
              variant="emerald"
            />
            <StatCard
              title="Rejected Submissions"
              value={loading ? "…" : stats?.rejected?.toString() ?? "0"}
              subtext="Declined governance approval"
              icon={XCircle}
              variant="rose"
            />
            <StatCard
              title="Review Incomplete"
              value={loading ? "…" : stats?.review_incomplete?.toString() ?? "0"}
              subtext="Outstanding findings unresolved"
              icon={Clock}
              variant="amber"
            />
            <StatCard
              title="High-Risk Findings"
              value={loading ? "…" : stats?.high_risk_findings?.toString() ?? "0"}
              subtext="Critical & high severity violations"
              icon={AlertTriangle}
              variant="rose"
            />
          </div>
        </div>

        {/* Workspace Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-3">
            <div className="w-10 h-10 rounded-lg bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-600">
              <BookOpen className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Brand Knowledge Base</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Upload guidelines, maintain verified product specifications, approved claims, and terminology rules.
            </p>
            <Link
              href="/brand-knowledge"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 pt-1"
            >
              <span>Explore Knowledge Hub</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Pre-Publication Submissions</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Submit drafts to detect prohibited terms, ungrounded claims, and outdated facts with traceable evidence.
            </p>
            <Link
              href="/submissions"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 pt-1"
            >
              <span>Manage Submissions</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Governance Analytics</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Real-time compliance rates, top violated terminology rules, and turnaround performance indicators.
            </p>
            <Link
              href="/analytics"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 pt-1"
            >
              <span>View Insights</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Real Audit Activity from Database */}
        <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-slate-500" />
              <h3 className="text-sm font-bold text-slate-900">Recent Workspace Audit Activity</h3>
            </div>
            {(isAdmin || isBrandManager) && (
              <Link href="/audit" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
                View Full Audit Log
              </Link>
            )}
          </div>
          {recentLogs.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">No recent audit activity recorded yet.</div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentLogs.map((log) => (
                <div key={log.id} className="py-3 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                      {log.event_type}
                    </span>
                    <span className="text-slate-600">
                      Entity: <span className="font-medium text-slate-800">{log.entity_type}</span>
                    </span>
                  </div>
                  <span className="text-slate-400 text-[11px]">{formatDate(log.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
