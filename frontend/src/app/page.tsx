"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { ShieldCheck } from "lucide-react";

export default function RootPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.replace("/dashboard");
      } else {
        router.replace("/login");
      }
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <div className="w-12 h-12 rounded-xl bg-brand-600 flex items-center justify-center text-white shadow-md shadow-brand-500/30 animate-bounce mb-4">
        <ShieldCheck className="w-7 h-7" />
      </div>
      <p className="text-sm font-medium text-slate-500">Loading BrandCanon AI...</p>
    </div>
  );
}

