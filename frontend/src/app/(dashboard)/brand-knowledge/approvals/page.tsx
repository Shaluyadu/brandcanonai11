"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  UserCheck,
  CheckCircle2,
  XCircle,
  Archive,
  Filter,
  ArrowLeft,
  FileText,
  BadgeCheck,
  SpellCheck,
  Clock
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { KnowledgeApproval } from "@/types/brand";

export default function KnowledgeApprovalsPage() {
  const [approvals, setApprovals] = useState<KnowledgeApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState("");
  const [decisionFilter, setDecisionFilter] = useState("");
  const [page, setPage] = useState(1);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const res = await api.brand.listApprovals({
        page,
        pageSize: 20,
        entityType: entityFilter || undefined,
        decision: decisionFilter || undefined,
      });
      if (res.success && res.data) {
        setApprovals(res.data.items);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [page, entityFilter, decisionFilter]);

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case "APPROVED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200"><CheckCircle2 className="w-3 h-3 text-emerald-600" /> Approved</span>;
      case "REJECTED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200"><XCircle className="w-3 h-3 text-rose-600" /> Rejected</span>;
      case "ARCHIVED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200"><Archive className="w-3 h-3 text-slate-500" /> Archived</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">{decision}</span>;
    }
  };

  const getEntityIcon = (type: string) => {
    switch (type) {
      case "DOCUMENT":
        return <FileText className="w-3.5 h-3.5 text-blue-600" />;
      case "FACT":
        return <BadgeCheck className="w-3.5 h-3.5 text-emerald-600" />;
      case "TERMINOLOGY_RULE":
        return <SpellCheck className="w-3.5 h-3.5 text-purple-600" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div>
      <Header
        title="Knowledge Approval History"
        description="Immutable audit trail of human governance approvals, rejections, and archival actions."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <Link
          href="/brand-knowledge"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Knowledge Hub</span>
        </Link>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">All Entity Types</option>
              <option value="DOCUMENT">Documents</option>
              <option value="FACT">Approved Facts</option>
              <option value="TERMINOLOGY_RULE">Terminology Rules</option>
            </select>
          </div>

          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">All Decisions</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="ARCHIVED">Archived</option>
          </select>
        </div>

        {/* Table */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          {loading ? (
            <div className="p-6">
              <LoadingSkeleton variant="table" />
            </div>
          ) : approvals.length === 0 ? (
            <div className="p-12">
              <EmptyState
                icon={UserCheck}
                title="No Approval Records"
                description="Decisions to approve, reject, or archive knowledge assets will appear in this audit log."
              />
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="py-3 px-4">Entity Type</th>
                  <th className="py-3 px-4">Decision</th>
                  <th className="py-3 px-4">Remarks / Reason</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {approvals.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2 font-semibold text-slate-900">
                        {getEntityIcon(item.entity_type)}
                        <span>{item.entity_type.replace("_", " ")}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        ID: {item.entity_id}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">{getDecisionBadge(item.decision)}</td>
                    <td className="py-3.5 px-4 text-slate-700 max-w-md">
                      {item.reason || <span className="text-slate-400 italic">No remarks provided</span>}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

