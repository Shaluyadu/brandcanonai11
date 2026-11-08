import React from "react";
import Link from "next/link";
import { LucideIcon, PlusCircle } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  actionHref?: string;
  onActionClick?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionText,
  actionHref,
  onActionClick,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-slate-200 bg-white">
      <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 mb-4 border border-slate-100">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm mb-6">{description}</p>
      {actionText && actionHref && (
        <Link
          href={actionHref}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          {actionText}
        </Link>
      )}
      {actionText && onActionClick && !actionHref && (
        <button
          onClick={onActionClick}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          {actionText}
        </button>
      )}
    </div>
  );
};

