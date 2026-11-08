import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  variant?: "default" | "brand" | "emerald" | "amber" | "rose";
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  variant = "default",
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case "brand":
        return {
          iconBox: "bg-brand-50 text-brand-600 border-brand-100",
        };
      case "emerald":
        return {
          iconBox: "bg-emerald-50 text-emerald-600 border-emerald-100",
        };
      case "amber":
        return {
          iconBox: "bg-amber-50 text-amber-600 border-amber-100",
        };
      case "rose":
        return {
          iconBox: "bg-rose-50 text-rose-600 border-rose-100",
        };
      default:
        return {
          iconBox: "bg-slate-50 text-slate-600 border-slate-100",
        };
    }
  };

  const styles = getVariantStyles();

  return (
    <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center border", styles.iconBox)}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
      {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
    </div>
  );
};

