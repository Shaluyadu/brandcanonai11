"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  Filter,
  Eye,
  RefreshCw,
  Trash2,
  ShieldCheck,
  XCircle,
  Archive,
  Layers
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { BrandDocument } from "@/types/brand";
import { cn } from "@/lib/utils";

export default function BrandDocumentsPage() {
  const { currentRole } = useAuth();
  const canUpload = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER";
  const canApprove = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER";

  const [documents, setDocuments] = useState<BrandDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await api.brand.listDocuments({
        page,
        pageSize: 15,
        approvalStatus: statusFilter || undefined,
      });
      if (res.success && res.data) {
        setDocuments(res.data.items);
        setTotal(res.data.total);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page, statusFilter]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.brand.uploadDocument(formData);
      if (res.success) {
        setUploadSuccess(`Document "${file.name}" uploaded and extracted successfully!`);
        fetchDocuments();
      } else {
        setUploadError(res.error?.message || "Upload failed");
      }
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleApprove = async (id: string) => {
    const reason = prompt("Enter approval remarks (optional):") || undefined;
    const res = await api.brand.approveDocument(id, reason);
    if (res.success) fetchDocuments();
  };

  const handleReject = async (id: string) => {
    const reason = prompt("Enter rejection reason:") || undefined;
    const res = await api.brand.rejectDocument(id, reason);
    if (res.success) fetchDocuments();
  };

  const handleReprocess = async (id: string) => {
    const res = await api.brand.reprocessDocument(id);
    if (res.success) fetchDocuments();
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;
    const res = await api.brand.deleteDocument(id);
    if (res.success) fetchDocuments();
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

  const getProcessingBadge = (status: string) => {
    switch (status) {
      case "EXTRACTED":
        return <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60">Extracted & Chunked</span>;
      case "PROCESSING":
        return <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200/60">Processing...</span>;
      case "UNSUPPORTED_SCANNED_DOCUMENT":
        return <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200/60">Scanned (No OCR)</span>;
      case "FAILED":
        return <span className="text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200/60">Extraction Failed</span>;
      default:
        return <span className="text-[11px] text-slate-600 bg-slate-50 px-2 py-0.5 rounded border">{status}</span>;
    }
  };

  return (
    <div>
      <Header
        title="Brand Guidelines & Reference Documents"
        description="Ingest, extract, chunk, and verify your brand documentation (.docx & text-based .pdf)."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Upload Card */}
        {canUpload && (
          <div className="bg-white border-2 border-dashed border-slate-300 rounded-xl p-6 hover:border-brand-500 transition-colors text-center shadow-xs">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
            />
            <div className="max-w-md mx-auto space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-brand-50 text-brand-600 flex items-center justify-center">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Upload Guidelines or Reference Documents</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Supported formats: Microsoft Word (<strong>.docx</strong>) or digital text-based (<strong>.pdf</strong>) up to 25MB.
                </p>
              </div>
              <button
                type="button"
                disabled={uploading}
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                <UploadCloud className="w-4 h-4" />
                <span>{uploading ? "Extracting & Chunking Document..." : "Select Document File"}</span>
              </button>
            </div>
          </div>
        )}

        {uploadSuccess && (
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        {uploadError && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Toolbar & Filter */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">All Approval Statuses</option>
              <option value="APPROVED">Approved (Active)</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="REJECTED">Rejected</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>
          <span className="text-xs text-slate-500">{total} document(s) total</span>
        </div>

        {/* Document Table */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          {loading ? (
            <div className="p-6">
              <LoadingSkeleton variant="table" />
            </div>
          ) : documents.length === 0 ? (
            <div className="py-12">
              <EmptyState
                icon={FileText}
                title="No Documents Found"
                description="Upload brand guideline documents or modify your filter criteria."
              />
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-4">Type / Size</th>
                  <th className="py-3 px-4">Processing</th>
                  <th className="py-3 px-4">Approval Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3.5 px-4">
                      <Link
                        href={`/brand-knowledge/documents/${doc.id}`}
                        className="font-medium text-slate-900 hover:text-brand-600 transition-colors flex items-center gap-2"
                      >
                        <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                        <span className="truncate max-w-xs">{doc.document_name}</span>
                      </Link>
                      <div className="text-[11px] text-slate-400 mt-0.5">Version {doc.current_version}</div>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">
                      <span className="uppercase font-semibold text-slate-700">{doc.file_type}</span> •{" "}
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3.5 px-4">{getProcessingBadge(doc.processing_status)}</td>
                    <td className="py-3.5 px-4">{getStatusBadge(doc.approval_status)}</td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <Link
                          href={`/brand-knowledge/documents/${doc.id}`}
                          title="View content preview & chunks"
                          className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-md transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>

                        {canApprove && doc.approval_status === "PENDING_APPROVAL" && (
                          <>
                            <button
                              onClick={() => handleApprove(doc.id)}
                              title="Approve Document"
                              className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-md transition-colors"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleReject(doc.id)}
                              title="Reject Document"
                              className="p-1.5 text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </>
                        )}

                        {canUpload && (
                          <>
                            <button
                              onClick={() => handleReprocess(doc.id)}
                              title="Reprocess & Re-chunk"
                              className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(doc.id, doc.document_name)}
                              title="Delete Document"
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
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

