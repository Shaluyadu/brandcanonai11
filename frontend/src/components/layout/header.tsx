"use client";

import React from "react";
import Link from "next/link";
import { PlusCircle, Shield, CheckCircle } from "lucide-react";
import { useAuth } from "@/context/auth-context";

interface HeaderProps {
  title: string;
  description?: string;
  actionText?: string;
  actionHref?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  description,
  actionText,
  actionHref,
}) => {
  const { activeOrganisation } = useAuth();

  return (
    <header className="h-16 px-8 border-b border-slate-200 bg-white flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h1>
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </div>

      <div className="flex items-center gap-3">
        {activeOrganisation && (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs text-slate-700">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-medium text-slate-800">{activeOrganisation.name}</span>
          </div>
        )}

        {actionText && actionHref && (
          <Link
            href={actionHref}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs shadow-brand-600/20 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>{actionText}</span>
          </Link>
        )}
      </div>
    </header>
  );
};

