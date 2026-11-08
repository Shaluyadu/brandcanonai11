"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  BarChart3,
  ShieldCheck,
  AlertTriangle,
  Clock,
  CheckCircle,
  FileText,
  RefreshCw,
  PieChart,
  Layers,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { StatCard } from "@/components/shared/stat-card";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { AnalyticsOverview } from "@/types/analytics";
import { useAuth } from "@/context/auth-context";

export default function AnalyticsPage() {
  const { activeOrganisation } = useAuth();
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.analytics.getOverview();
      if (res.success && res.data) {
        setData(res.data);
      }
    } catch (err) {
      console.error("Failed to load analytics", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <div>
      <Header
        title="Governance Insights & Analytics"
        description="Empirical brand compliance metrics, recurring terminology violations, and approval turnaround performance."
      />
      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Banner */}
        <div className="p-5 rounded-xl bg-slate-900 text-white flex items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-300">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight">Enterprise Governance Telemetry</h3>
              <p className="text-xs text-slate-300">
                Metrics are aggregated live from verified content reviews and findings in {activeOrganisation?.name || "your organization"}.
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchAnalytics()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {/* 4 Primary KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Brand Compliance Rate"
            value={loading ? "…" : `${data?.compliance_rate ?? 0}%`}
            subtext="Clean reviews with 0 high/critical issues"
            icon={ShieldCheck}
            variant="emerald"
          />
          <StatCard
            title="Total Submissions"
            value={loading ? "…" : (data?.total_submissions_analyzed ?? 0).toString()}
            subtext="Submissions evaluated by AI engine"
            icon={FileText}
            variant="default"
          />
          <StatCard
            title="Issues Detected"
            value={loading ? "…" : (data?.total_findings_detected ?? 0).toString()}
            subtext="Prohibited terms & ungrounded claims"
            icon={AlertTriangle}
            variant="rose"
          />
          <StatCard
            title="Average Turnaround"
            value={loading ? "…" : `${data?.average_turnaround_hours ?? 0}h`}
            subtext="Mean submission-to-decision time"
            icon={Clock}
            variant="amber"
          />
        </div>

        {/* Deep Dive Breakdown Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Top Violated Brand Rules (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand-600" />
                <h3 className="text-sm font-bold text-slate-900">Top Violated Brand Guidelines</h3>
              </div>
              <span className="text-[11px] text-slate-400">Ranked by frequency</span>
            </div>

            {loading ? (
              <div className="space-y-2 py-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : !data || data.top_violated_rules.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                No terminology or claim violations recorded yet. All reviewed copy satisfies active brand guidelines.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {data.top_violated_rules.map((rule, idx) => (
                  <div key={idx} className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <span className="w-5 text-center font-bold text-slate-400 font-mono text-[11px]">
                        #{idx + 1}
                      </span>
                      <div>
                        <div className="font-mono font-semibold text-slate-900">
                          &ldquo;{rule.rule_term}&rdquo;
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Category: {rule.category}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                        {rule.severity}
                      </span>
                      <span className="font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md text-xs font-mono">
                        {rule.count} hit{rule.count > 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Publishing Channels & Severity Breakdown (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Channel Breakdown */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-xs">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <Layers className="w-4 h-4 text-brand-600" />
                <h3 className="text-sm font-bold text-slate-900">Submissions by Channel</h3>
              </div>

              {loading ? (
                <div className="space-y-2 py-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-6 bg-slate-100 rounded animate-pulse" />
                  ))}
                </div>
              ) : !data || Object.keys(data.violations_by_channel).length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400">No channel data recorded.</div>
              ) : (
                <div className="space-y-3">
                  {Object.entries(data.violations_by_channel).map(([channel, count]) => (
                    <div key={channel} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700">{channel}</span>
                        <span className="font-bold text-slate-900">{count}</span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-brand-600 h-full rounded-full transition-all"
                          style={{
                            width: `${Math.min(
                              100,
                              data.total_submissions_analyzed > 0
                                ? (count / data.total_submissions_analyzed) * 100
                                : 0
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Severity Distribution */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-xs">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                <PieChart className="w-4 h-4 text-brand-600" />
                <h3 className="text-sm font-bold text-slate-900">Finding Severity Distribution</h3>
              </div>

              {loading ? (
                <div className="h-16 bg-slate-100 rounded animate-pulse" />
              ) : !data ? (
                <div className="py-4 text-center text-xs text-slate-400">No findings data.</div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(data.violations_by_severity).map(([sev, count]) => (
                    <div key={sev} className="p-3 rounded-lg border border-slate-100 bg-slate-50/50">
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{sev}</div>
                      <div className="text-lg font-bold text-slate-900 mt-0.5">{count}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
