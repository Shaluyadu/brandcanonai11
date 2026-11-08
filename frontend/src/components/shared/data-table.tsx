// src/components/shared/data-table.tsx
"use client";

import React from "react";
import { EmptyState } from "@/components/shared/empty-state";
import { ArrowUpDown, ArrowUp, ArrowDown, Inbox } from "lucide-react";

export type Column<T> = {
  Header: string;
  accessor: keyof T;
  sortable?: boolean;
  Cell?: (row: T) => React.ReactNode;
};

type Props<T extends object> = {
  columns: Column<T>[];
  data: T[];
  loading: boolean;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  onSortChange?: (sortBy: string, sortOrder: "asc" | "desc") => void;
  emptyTitle?: string;
  emptyDescription?: string;
};

export default function DataTable<T extends object>({
  columns,
  data,
  loading,
  sortBy,
  sortOrder,
  onSortChange,
  emptyTitle = "No records found",
  emptyDescription = "Try adjusting your search or filters to locate data.",
}: Props<T>) {
  const handleHeaderClick = (col: Column<T>) => {
    if (!col.sortable || !onSortChange) return;
    const newOrder = sortBy === col.accessor && sortOrder === "asc" ? "desc" : "asc";
    onSortChange(col.accessor as string, newOrder);
  };

  if (loading) {
    return (
      <div className="space-y-3 p-4 bg-white rounded-xl border border-slate-200">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-4 animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-1/4" />
            <div className="h-4 bg-slate-100 rounded w-1/4" />
            <div className="h-4 bg-slate-200 rounded w-1/4" />
            <div className="h-4 bg-slate-100 rounded w-1/4" />
          </div>
        ))}
      </div>
    );
  }

  if (!loading && data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <EmptyState
          icon={Inbox}
          title={emptyTitle}
          description={emptyDescription}
        />
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs">
      <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
        <thead className="bg-slate-50/80 text-slate-700 font-semibold">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.accessor)}
                className={`px-4 py-3.5 ${col.sortable ? "cursor-pointer select-none hover:text-brand-600 transition-colors" : ""}`}
                onClick={() => handleHeaderClick(col)}
              >
                <div className="inline-flex items-center gap-1.5">
                  <span>{col.Header}</span>
                  {col.sortable && (
                    <span className="text-slate-400">
                      {sortBy === col.accessor ? (
                        sortOrder === "asc" ? (
                          <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                        ) : (
                          <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                        )
                      ) : (
                        <ArrowUpDown className="w-3.5 h-3.5 opacity-40 hover:opacity-100" />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
              {columns.map((col) => (
                <td key={String(col.accessor)} className="px-4 py-3 text-slate-700">
                  {col.Cell ? col.Cell(row) : String(row[col.accessor] ?? "-")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
