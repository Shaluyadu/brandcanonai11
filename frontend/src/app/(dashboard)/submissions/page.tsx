"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileCheck2,
  PlusCircle,
  Search,
  Filter,
  ArrowRight,
  Sparkles,
  RefreshCw,
  X,
  FileText,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import DataTable, { Column } from "@/components/shared/data-table";
import { api } from "@/lib/api";
import { SubmissionListItem } from "@/types/submission";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";

export default function ContentSubmissionsPage() {
  const { activeOrganisation } = useAuth();
  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [channelFilter, setChannelFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Create submission modal
  const [modalOpen, setModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newChannel, setNewChannel] = useState("WEB");
  const [newType, setNewType] = useState("ARTICLE");
  const [newContent, setNewContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const fetchSubmissions = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.governance.getSubmissions({
        page,
        pageSize,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        channel: channelFilter || undefined,
        sortBy,
        sortOrder,
      });

      if (res.success && res.data) {
        setSubmissions(res.data.items);
        setTotal(res.data.total);
        setTotalPages(res.data.total_pages);
      }
    } catch (err) {
      console.error("Failed to load submissions", err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, statusFilter, channelFilter, sortBy, sortOrder]);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  const handleSortChange = (col: string, order: "asc" | "desc") => {
    setSortBy(col);
    setSortOrder(order);
  };

  const handleCreateSubmission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) {
      setFormError("Title and content copy are required.");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      const res = await api.governance.createSubmission({
        title: newTitle.trim(),
        content_type: newType,
        publishing_channel: newChannel,
        content_text: newContent.trim(),
      });
      if (res.success) {
        setModalOpen(false);
        setNewTitle("");
        setNewContent("");
        fetchSubmissions();
      } else {
        setFormError(res.error?.message || "Failed to submit draft");
      }
    } catch (err: any) {
      setFormError(err.message || "An unexpected error occurred");
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "CHANGES_REQUESTED":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "REJECTED":
        return "bg-rose-50 text-rose-700 border-rose-200";
      case "SUBMITTED":
        return "bg-blue-50 text-blue-700 border-blue-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const columns: Column<SubmissionListItem>[] = [
    {
      Header: "Title",
      accessor: "title",
      sortable: true,
      Cell: (row) => (
        <div>
          <Link
            href={`/review?id=${row.id}`}
            className="font-semibold text-brand-600 hover:text-brand-800 hover:underline"
          >
            {row.title}
          </Link>
          {row.campaign_name && (
            <div className="text-[11px] text-slate-400">Campaign: {row.campaign_name}</div>
          )}
        </div>
      ),
    },
    {
      Header: "Channel",
      accessor: "publishing_channel",
      sortable: true,
      Cell: (row) => (
        <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-700 border border-slate-200 font-medium">
          {row.publishing_channel}
        </span>
      ),
    },
    {
      Header: "Status",
      accessor: "current_status",
      sortable: true,
      Cell: (row) => (
        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadge(
            row.current_status
          )}`}
        >
          {row.current_status.replace("_", " ")}
        </span>
      ),
    },
    {
      Header: "AI Review",
      accessor: "latest_review_status",
      Cell: (row) => (
        <span className="text-slate-600 text-xs">
          {row.latest_review_status || "Incomplete"}
        </span>
      ),
    },
    {
      Header: "Created",
      accessor: "created_at",
      sortable: true,
      Cell: (row) => (
        <span className="text-slate-400 text-xs">{formatDate(row.created_at)}</span>
      ),
    },
    {
      Header: "Actions",
      accessor: "id",
      Cell: (row) => (
        <Link
          href={`/review?id=${row.id}`}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-brand-50 text-slate-700 hover:text-brand-600 text-xs font-semibold transition-colors"
        >
          <span>Review Studio</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      ),
    },
  ];

  return (
    <div>
      <Header
        title="Content Submissions"
        description="Draft, version, and submit marketing and corporate copy for automated pre-publication governance."
      />
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Actions bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="Search submissions..."
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            >
              <option value="">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="CHANGES_REQUESTED">Changes Requested</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="DRAFT">Draft</option>
            </select>

            {/* Channel Filter */}
            <select
              value={channelFilter}
              onChange={(e) => {
                setChannelFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            >
              <option value="">All Channels</option>
              <option value="WEB">Web</option>
              <option value="EMAIL">Email</option>
              <option value="SOCIAL">Social</option>
              <option value="BLOG_POST">Blog Post</option>
              <option value="PRINT">Print</option>
            </select>

            <button
              onClick={() => fetchSubmissions()}
              title="Refresh"
              className="p-2 text-slate-500 hover:text-slate-700 bg-white border border-slate-200 rounded-lg"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Submission</span>
          </button>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={submissions}
          loading={loading}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortChange={handleSortChange}
          emptyTitle="No Submissions Found"
          emptyDescription="There are no content submissions matching your criteria. Click 'New Submission' to create one."
        />

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-2 text-xs text-slate-500">
            <div>
              Showing page <span className="font-semibold text-slate-800">{page}</span> of{" "}
              <span className="font-semibold text-slate-800">{totalPages}</span> ({total} items)
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 border border-slate-200 rounded-lg bg-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 font-medium"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1.5 border border-slate-200 rounded-lg bg-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 font-medium"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New Submission Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-brand-600" />
                <h3 className="text-base font-bold text-slate-900">New Content Submission</h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubmission} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Submission Title *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Q4 Cloud Product Announcement"
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Publishing Channel
                  </label>
                  <select
                    value={newChannel}
                    onChange={(e) => setNewChannel(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white"
                  >
                    <option value="WEB">Web</option>
                    <option value="EMAIL">Email</option>
                    <option value="SOCIAL">Social Media</option>
                    <option value="BLOG_POST">Blog Post</option>
                    <option value="PRINT">Print</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Content Type
                  </label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white"
                  >
                    <option value="ARTICLE">Article / Press Release</option>
                    <option value="PRODUCT_COPY">Product Description</option>
                    <option value="MARKETING_EMAIL">Marketing Email</option>
                    <option value="LANDING_PAGE">Landing Page</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Content Draft / Copy *
                </label>
                <textarea
                  required
                  rows={8}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Paste or write your full marketing copy here. Automated brand checks will detect prohibited terminology and unverified claims..."
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
                >
                  {submitting ? "Analyzing & Submitting..." : "Submit Draft for Review"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
