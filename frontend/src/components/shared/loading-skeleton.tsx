import React from "react";
import { cn } from "@/lib/utils";

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return <div className={cn("animate-pulse bg-slate-200/80 rounded", className)} />;
};

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-5 rounded-xl border border-slate-200 bg-white space-y-3">
            <div className="flex justify-between items-center">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-8 w-8 rounded-lg" />
            </div>
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
      <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-4">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
};

export const LoadingSkeleton: React.FC<{ variant?: "card" | "table" | "list"; count?: number }> = ({
  variant = "card",
  count = 3,
}) => {
  if (variant === "table") {
    return (
      <div className="space-y-3 p-4">
        <div className="flex justify-between pb-3 border-b border-slate-100">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
        {[...Array(count)].map((_, i) => (
          <div key={i} className="flex justify-between py-2 border-b border-slate-50">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div className="p-5 rounded-xl border border-slate-200 bg-white space-y-3">
        <div className="flex justify-between items-center">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-8 w-8 rounded-lg" />
        </div>
        <Skeleton className="h-7 w-20" />
        <Skeleton className="h-3 w-36" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {[...Array(count)].map((_, i) => (
        <Skeleton key={i} className="h-8 w-full rounded-md" />
      ))}
    </div>
  );
};
