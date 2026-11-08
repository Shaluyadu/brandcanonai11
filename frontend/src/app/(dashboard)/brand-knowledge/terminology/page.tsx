"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  SpellCheck,
  Plus,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Archive,
  Trash2,
  Filter,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Sliders,
  Check
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { TerminologyRule, TerminologyMatch } from "@/types/brand";

export default function TerminologyPage() {
  const { currentRole } = useAuth();
  const canManage = currentRole === "ADMIN" || currentRole === "BRAND_MANAGER";

  const [rules, setRules] = useState<TerminologyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Playground tester state
  const [testText, setTestText] = useState("");
  const [testMatches, setTestMatches] = useState<TerminologyMatch[]>([]);
  const [checking, setChecking] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    prohibited_term: "",
    preferred_term: "",
    match_type: "WHOLE_WORD",
    severity: "HIGH",
    case_sensitive: false,
    category: "BRAND_IDENTITY",
    description: "",
  });

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await api.brand.listTerminology({
        severity: severityFilter || undefined,
      });
      if (res.success && res.data) {
        setRules(res.data.items);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [severityFilter]);

  const handleTestCheck = async () => {
    if (!testText.trim()) return;
    setChecking(true);
    try {
      const res = await api.brand.checkTerminology(testText);
      if (res.success && res.data) {
        setTestMatches(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setChecking(false);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const payload: Partial<TerminologyRule> = {
      prohibited_term: formData.prohibited_term.trim(),
      preferred_term: formData.preferred_term.trim(),
      match_type: formData.match_type,
      severity: formData.severity,
      case_sensitive: formData.case_sensitive,
      category: formData.category,
      description: formData.description.trim() || undefined,
    };

    try {
      const res = await api.brand.createTerminology(payload);
      if (res.success) {
        setShowModal(false);
        setFormData({
          prohibited_term: "",
          preferred_term: "",
          match_type: "WHOLE_WORD",
          severity: "HIGH",
          case_sensitive: false,
          category: "BRAND_IDENTITY",
          description: "",
        });
        fetchRules();
      } else {
        setErrorMsg(res.error?.message || "Failed to create terminology rule");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit rule");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this terminology rule?")) return;
    const res = await api.brand.deleteTerminology(id);
    if (res.success) fetchRules();
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "HIGH":
        return <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">High</span>;
      case "MEDIUM":
        return <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">Medium</span>;
      case "LOW":
        return <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">Low</span>;
      default:
        return <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-800">{severity}</span>;
    }
  };

  return (
    <div>
      <Header
        title="Terminology Rules & Linter"
        description="Enforce preferred vocabulary, ban outdated/risky terminology, and run deterministic compliance scans."
      />

      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Interactive Text Checker Playground */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <h3 className="text-sm font-bold text-slate-900">Deterministic Terminology Scanner</h3>
            </div>
            <span className="text-[11px] text-slate-400">Tests against active organisation rules</span>
          </div>

          <div className="space-y-3">
            <textarea
              rows={3}
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              placeholder="Paste draft copy here to scan for prohibited buzzwords, deprecated terms, or unauthorized claims..."
              className="w-full px-3.5 py-2.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
            <div className="flex justify-between items-center">
              <div className="text-xs text-slate-500">
                {testMatches.length > 0 && (
                  <span className="font-semibold text-rose-600">
                    Found {testMatches.length} prohibited terminology violation(s)
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleTestCheck}
                disabled={checking || !testText.trim()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition-colors shadow-xs disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{checking ? "Scanning Text..." : "Scan Content"}</span>
              </button>
            </div>
          </div>

          {/* Matches Output */}
          {testMatches.length > 0 && (
            <div className="pt-3 border-t border-slate-100 space-y-2">
              {testMatches.map((m, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-rose-50/70 border border-rose-200/80 flex items-center justify-between text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-rose-800 line-through">&ldquo;{m.matched_text}&rdquo;</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60">
                        &ldquo;{m.preferred_term}&rdquo;
                      </span>
                      {getSeverityBadge(m.severity)}
                    </div>
                    {m.description && <div className="text-[11px] text-slate-600">{m.description}</div>}
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Index [{m.match_start}:{m.match_end}]
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Toolbar & Filters */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">All Severities</option>
              <option value="HIGH">High Severity</option>
              <option value="MEDIUM">Medium Severity</option>
              <option value="LOW">Low Severity</option>
            </select>
          </div>

          {canManage && (
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Add Terminology Rule</span>
            </button>
          )}
        </div>

        {/* Rules Table */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          {loading ? (
            <div className="p-6">
              <LoadingSkeleton variant="table" />
            </div>
          ) : rules.length === 0 ? (
            <div className="p-12">
              <EmptyState
                icon={SpellCheck}
                title="No Terminology Rules Configured"
                description="Add rules to enforce your brand vocabulary and prohibit non-compliant words."
              />
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="py-3 px-4">Prohibited Term</th>
                  <th className="py-3 px-4">Preferred Replacement</th>
                  <th className="py-3 px-4">Match Mode</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-rose-700 line-through">
                      {rule.prohibited_term}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-emerald-700">
                      {rule.preferred_term}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <span className="font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded">
                        {rule.match_type}
                      </span>
                      {rule.case_sensitive && (
                        <span className="ml-1 text-[10px] text-slate-400">(case-sensitive)</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">{getSeverityBadge(rule.severity)}</td>
                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-[11px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60">
                        {rule.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {canManage && (
                        <button
                          onClick={() => handleDelete(rule.id)}
                          title="Delete Rule"
                          className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-md"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Modal: Create Terminology Rule */}
        {showModal && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-bold text-slate-900">Add Terminology Rule</h3>
                <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                  ✕
                </button>
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleCreateRule} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Prohibited Term *</label>
                  <input
                    type="text"
                    required
                    value={formData.prohibited_term}
                    onChange={(e) => setFormData({ ...formData, prohibited_term: e.target.value })}
                    placeholder="e.g. cheap, ultra-fast, synergy"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Preferred Term *</label>
                  <input
                    type="text"
                    required
                    value={formData.preferred_term}
                    onChange={(e) => setFormData({ ...formData, preferred_term: e.target.value })}
                    placeholder="e.g. affordable, high-performance, collaboration"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Match Type</label>
                    <select
                      value={formData.match_type}
                      onChange={(e) => setFormData({ ...formData, match_type: e.target.value })}
                      className="w-full px-2.5 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                    >
                      <option value="WHOLE_WORD">WHOLE_WORD (Safe)</option>
                      <option value="EXACT">EXACT</option>
                      <option value="PHRASE">PHRASE</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Severity</label>
                    <select
                      value={formData.severity}
                      onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                      className="w-full px-2.5 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                    >
                      <option value="HIGH">HIGH</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="LOW">LOW</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="case_sensitive"
                    checked={formData.case_sensitive}
                    onChange={(e) => setFormData({ ...formData, case_sensitive: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <label htmlFor="case_sensitive" className="text-slate-700 select-none">
                    Case-sensitive matching
                  </label>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Reason / Description</label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Why this term should be avoided..."
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3.5 py-2 font-medium text-slate-600 hover:text-slate-900 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs"
                  >
                    Create Rule
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

