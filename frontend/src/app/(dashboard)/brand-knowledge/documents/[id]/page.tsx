"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  Layers,
  Clock,
  CheckCircle2,
  XCircle,
  Archive,
  RefreshCw,
  Hash,
  BookOpen,
  Calendar,
  AlertCircle
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { BrandDocument, DocumentContent } from "@/types/brand";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params?.id as string;
  const { currentRole } = useAuth();
  const canApprove = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER";

  const [doc, setDoc] = useState<BrandDocument | null>(null);
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"preview" | "chunks" | "versions">("preview");

  const loadDocumentData = async () => {
    if (!documentId) return;
    try {
      setLoading(true);
      const [docRes, contentRes] = await Promise.all([
        api.brand.getDocument(documentId),
        api.brand.getDocumentContent(documentId),
      ]);
      if (docRes.success && docRes.data) {
        setDoc(docRes.data);
      }
      if (contentRes.success && contentRes.data) {
        setContent(contentRes.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocumentData();
  }, [documentId]);

  const handleApprove = async () => {
    const reason = prompt("Enter approval remarks (optional):") || undefined;
    const res = await api.brand.approveDocument(documentId, reason);
    if (res.success) loadDocumentData();
  };

  const handleReject = async () => {
    const reason = prompt("Enter rejection reason:") || undefined;
    const res = await api.brand.rejectDocument(documentId, reason);
    if (res.success) loadDocumentData();
  };

  const handleReprocess = async () => {
    const res = await api.brand.reprocessDocument(documentId);
    if (res.success) loadDocumentData();
  };

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="table" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-base font-semibold text-slate-800">Document Not Found</h3>
        <Link
          href="/brand-knowledge/documents"
          className="inline-flex items-center gap-1.5 text-xs text-brand-600 font-semibold"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Documents
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Header
        title={doc.document_name}
        description={`Version ${doc.current_version} • ${(doc.file_size / 1024).toFixed(1)} KB • Ingested on ${new Date(doc.created_at).toLocaleDateString()}`}
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Link
            href="/brand-knowledge/documents"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Documents</span>
          </Link>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleReprocess}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
              <span>Reprocess</span>
            </button>

            {canApprove && doc.approval_status !== "APPROVED" && (
              <button
                onClick={handleApprove}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-xs"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Approve Knowledge</span>
              </button>
            )}

            {canApprove && doc.approval_status !== "REJECTED" && (
              <button
                onClick={handleReject}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>
            )}
          </div>
        </div>

        {/* Status Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Approval Status</div>
            <div className="mt-1 font-semibold text-sm text-slate-900">{doc.approval_status}</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Extraction Status</div>
            <div className="mt-1 font-semibold text-sm text-slate-900">{content?.extraction_status || doc.processing_status}</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Pages</div>
            <div className="mt-1 font-semibold text-sm text-slate-900">{content?.total_pages ?? 1}</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Chunks</div>
            <div className="mt-1 font-semibold text-sm text-slate-900">{content?.total_chunks ?? 0}</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-200 flex items-center gap-6">
          <button
            onClick={() => setActiveTab("preview")}
            className={`pb-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "preview"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Extracted Text Preview
          </button>
          <button
            onClick={() => setActiveTab("chunks")}
            className={`pb-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "chunks"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Searchable Chunks ({content?.chunks.length ?? 0})
          </button>
          <button
            onClick={() => setActiveTab("versions")}
            className={`pb-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "versions"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Version History ({doc.versions?.length ?? 1})
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "preview" && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-500 border-b border-slate-100 pb-3">
              <span>Normalized Document Text</span>
              <span>Showing preview (up to 5,000 characters)</span>
            </div>
            <pre className="whitespace-pre-wrap font-sans text-xs text-slate-800 leading-relaxed max-h-[600px] overflow-y-auto bg-slate-50/70 p-4 rounded-lg border border-slate-100">
              {content?.text_preview || "No text could be extracted from this document."}
            </pre>
          </div>
        )}

        {activeTab === "chunks" && (
          <div className="space-y-4">
            {content?.chunks.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-xs text-slate-500">
                No chunks generated yet. Try re-processing the document.
              </div>
            ) : (
              content?.chunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-brand-600 bg-brand-50 px-2 py-0.5 rounded border border-brand-200/50">
                        Chunk #{chunk.chunk_index + 1}
                      </span>
                      {chunk.source_page && (
                        <span className="text-slate-500 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
                          Page {chunk.source_page}
                        </span>
                      )}
                      {chunk.source_location && (
                        <span className="text-slate-500 text-[11px]">
                          {chunk.source_location}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-slate-400">
                      SHA: {chunk.content_hash.slice(0, 10)}...
                    </span>
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-wrap bg-slate-50/50 p-3 rounded-lg border border-slate-100">
                    {chunk.content}
                  </p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "versions" && (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Extraction</th>
                  <th className="py-3 px-4">Pages / Chunks</th>
                  <th className="py-3 px-4">Content Hash</th>
                  <th className="py-3 px-4">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {doc.versions?.map((v) => (
                  <tr key={v.id}>
                    <td className="py-3 px-4 font-semibold text-slate-900">v{v.version_number}</td>
                    <td className="py-3 px-4">{v.extraction_status}</td>
                    <td className="py-3 px-4 text-slate-600">{v.total_pages} pages • {v.total_chunks} chunks</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{v.content_hash.slice(0, 16)}...</td>
                    <td className="py-3 px-4 text-slate-500">{new Date(v.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

