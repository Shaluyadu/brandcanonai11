"use client";

import React, { useEffect, useState } from "react";
import { History, Shield, Filter, Search, ChevronRight, FileJson } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { AuditLog } from "@/types/audit";
import { formatDate } from "@/lib/utils";

export default function AuditHistoryPage() {
  const { activeOrganisation, isAdmin, isBrandManager } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const res = await api.audit.list({
        page,
        pageSize: 15,
        eventType: eventTypeFilter.trim() || undefined,
      });
      if (res.success && res.data) {
        setLogs(res.data.items);
        setTotal(res.data.total);
      }
    } catch (err) {
      console.error("Failed to load audit logs", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, eventTypeFilter, activeOrganisation]);

  return (
    <div>
      <Header
        title="Audit History"
        description="Immutable record of security events, knowledge approvals, content revisions, and role changes."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={eventTypeFilter}
              onChange={(e) => {
                setEventTypeFilter(e.target.value);
                setPage(1);
              }}
              placeholder="Filter by event type (e.g. AUTH, MEMBER)..."
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500 w-64"
            />
          </div>
          <div className="text-xs text-slate-500 font-medium">
            Total Logged Events: <span className="text-slate-900 font-semibold">{total}</span>
          </div>
        </div>

        {/* Audit Log Table */}
        <div className="border border-slate-200 rounded-xl bg-white shadow-xs overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-6">Timestamp</th>
                <th className="py-3 px-6">Event Type</th>
                <th className="py-3 px-6">Target Entity</th>
                <th className="py-3 px-6">Entity ID</th>
                <th className="py-3 px-6 text-right">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    Loading audit records...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No audit records matching your criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  return (
                    <React.Fragment key={log.id}>
                      <tr className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3.5 px-6 text-slate-500 font-mono text-[11px]">
                          {formatDate(log.created_at)}
                        </td>
                        <td className="py-3.5 px-6">
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-800 font-semibold border border-slate-200">
                            {log.event_type}
                          </span>
                        </td>
                        <td className="py-3.5 px-6 font-medium text-slate-800">{log.entity_type}</td>
                        <td className="py-3.5 px-6 font-mono text-[11px] text-slate-500 truncate max-w-[150px]">
                          {log.entity_id}
                        </td>
                        <td className="py-3.5 px-6 text-right">
                          <button
                            onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-600 hover:text-brand-700"
                          >
                            <FileJson className="w-3.5 h-3.5" />
                            <span>{isExpanded ? "Hide" : "Inspect"}</span>
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-slate-50/80">
                          <td colSpan={5} className="p-4 px-6">
                            <pre className="text-[11px] font-mono p-3 rounded-lg bg-slate-900 text-slate-100 overflow-x-auto">
                              {JSON.stringify(log.metadata_json, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

