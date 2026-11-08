"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldCheck,
  LayoutDashboard,
  Sparkles,
  FileCheck2,
  BookOpen,
  LineChart,
  History,
  Users,
  Settings,
  LogOut,
  Building2,
  ChevronDown,
  CheckCircle2,
  FileText,
  BadgeCheck,
  SpellCheck,
  UserCheck,
  Sliders
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  allowedRoles?: ("ADMIN" | "BRAND_MANAGER" | "CREATOR" | "REVIEWER")[];
  badge?: string;
  subItems?: { label: string; href: string; icon: React.ComponentType<{ className?: string }> }[];
}

const navItems: NavItem[] = [
  {
    label: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Brand Knowledge Hub",
    href: "/brand-knowledge",
    icon: BookOpen,
    subItems: [
      { label: "Hub Overview", href: "/brand-knowledge", icon: BookOpen },
      { label: "Brand Profile", href: "/brand-knowledge/profile", icon: Sliders },
      { label: "Guidelines & Docs", href: "/brand-knowledge/documents", icon: FileText },
      { label: "Approved Facts", href: "/brand-knowledge/facts", icon: BadgeCheck },
      { label: "Terminology Rules", href: "/brand-knowledge/terminology", icon: SpellCheck },
      { label: "Knowledge Approvals", href: "/brand-knowledge/approvals", icon: UserCheck },
    ]
  },
  {
    label: "Content Submissions",
    href: "/submissions",
    icon: FileCheck2,
  },
  {
    label: "AI Review Studio",
    href: "/review",
    icon: Sparkles,
  },
  {
    label: "Approval Workspace",
    href: "/approvals",
    icon: CheckCircle2,
  },
  {
    label: "Governance Insights",
    href: "/analytics",
    icon: LineChart,
    allowedRoles: ["ADMIN", "BRAND_MANAGER"],
  },
  {
    label: "Audit History",
    href: "/audit",
    icon: History,
    allowedRoles: ["ADMIN", "BRAND_MANAGER"],
  },
  {
    label: "Members & Roles",
    href: "/members",
    icon: Users,
    allowedRoles: ["ADMIN"],
  },
  {
    label: "Workspace Settings",
    href: "/workspace",
    icon: Settings,
    allowedRoles: ["ADMIN", "BRAND_MANAGER"],
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user, activeOrganisation, currentRole, permittedOrganisations, switchOrganisation, logout } = useAuth();
  const [showOrgDropdown, setShowOrgDropdown] = useState(false);

  const getRoleBadgeColor = (role?: string | null) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-100 text-purple-700 border-purple-200";
      case "BRAND_MANAGER":
        return "bg-orange-100 text-orange-700 border-orange-200";
      case "CREATOR":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "REVIEWER":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const filteredNav = navItems.filter((item) => {
    if (!item.allowedRoles) return true;
    if (!currentRole) return false;
    return item.allowedRoles.includes(currentRole);
  });

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 px-5 border-b border-slate-200 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white shadow-sm shadow-brand-500/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-slate-900 tracking-tight text-base">BrandCanon</span>
            <span className="ml-1 text-xs font-semibold px-1.5 py-0.5 rounded bg-brand-100 text-brand-700">AI</span>
          </div>
        </Link>
      </div>

      {/* Workspace Switcher */}
      <div className="px-4 py-3 border-b border-slate-100 relative">
        <button
          onClick={() => setShowOrgDropdown(!showOrgDropdown)}
          className="w-full flex items-center justify-between p-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100/80 transition-colors text-left"
        >
          <div className="flex items-center gap-2 overflow-hidden">
            <Building2 className="w-4 h-4 text-slate-500 shrink-0" />
            <span className="text-xs font-medium text-slate-800 truncate">
              {activeOrganisation?.name || "Active Workspace"}
            </span>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        </button>

        {showOrgDropdown && permittedOrganisations.length > 0 && (
          <div className="absolute top-full left-4 right-4 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-50 py-1">
            <div className="px-3 py-1.5 text-[10px] font-semibold tracking-wider uppercase text-slate-400">
              Workspaces
            </div>
            {permittedOrganisations.map((org) => (
              <button
                key={org.id}
                onClick={() => {
                  switchOrganisation(org.id);
                  setShowOrgDropdown(false);
                }}
                className={cn(
                  "w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors",
                  org.id === activeOrganisation?.id ? "font-semibold text-brand-600 bg-brand-50/50" : "text-slate-700"
                )}
              >
                <span className="truncate">{org.name}</span>
                {org.id === activeOrganisation?.id && <CheckCircle2 className="w-3.5 h-3.5 text-brand-600" />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        <div className="px-3 pb-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Platform
        </div>
        {filteredNav.map((item) => {
          const isMainActive = item.href === "/brand-knowledge"
            ? pathname.startsWith("/brand-knowledge")
            : pathname === item.href;
          const Icon = item.icon;
          const hasSub = item.subItems && isMainActive;

          return (
            <div key={item.href} className="space-y-0.5">
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all group",
                  isMainActive
                    ? "bg-brand-50 text-brand-700 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/70"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isMainActive ? "text-brand-600" : "text-slate-400 group-hover:text-slate-600"
                  )}
                />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-auto text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
                    {item.badge}
                  </span>
                )}
              </Link>

              {/* Sub-navigation for Brand Knowledge Hub */}
              {hasSub && (
                <div className="pl-6 pr-1 py-1 space-y-0.5 border-l-2 border-brand-100 ml-4 mt-1">
                  {item.subItems!.map((sub) => {
                    const isSubActive = pathname === sub.href;
                    const SubIcon = sub.icon;
                    return (
                      <Link
                        key={sub.href}
                        href={sub.href}
                        className={cn(
                          "flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all",
                          isSubActive
                            ? "bg-brand-100/70 text-brand-800 font-semibold"
                            : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
                        )}
                      >
                        <SubIcon className={cn("w-3.5 h-3.5", isSubActive ? "text-brand-600" : "text-slate-400")} />
                        <span>{sub.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* User Footer */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/50">
        <div className="flex items-center justify-between p-2 rounded-lg border border-slate-200/80 bg-white">
          <div className="overflow-hidden mr-2">
            <div className="text-xs font-semibold text-slate-900 truncate">{user?.full_name || "User"}</div>
            <div className="text-[11px] text-slate-500 truncate">{user?.email}</div>
            <div className="mt-1">
              <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded border inline-block", getRoleBadgeColor(currentRole))}>
                {currentRole?.replace("_", " ") || "MEMBER"}
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
