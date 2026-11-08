"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { User, Organisation, RoleType, MeResponseData } from "@/types/auth";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  activeOrganisation: Organisation | null;
  currentRole: RoleType | null;
  permittedOrganisations: Organisation[];
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isBrandManager: boolean;
  isCreator: boolean;
  isReviewer: boolean;
  hasPermission: (allowedRoles: RoleType[]) => boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    organisation_name?: string;
  }) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  switchOrganisation: (orgId: string) => Promise<void>;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [activeOrganisation, setActiveOrganisation] = useState<Organisation | null>(null);
  const [currentRole, setCurrentRole] = useState<RoleType | null>(null);
  const [permittedOrganisations, setPermittedOrganisations] = useState<Organisation[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshMe = useCallback(async () => {
    try {
      const res = await api.auth.me();
      if (res.success && res.data) {
        setUser(res.data.user);
        setActiveOrganisation(res.data.active_organisation);
        setCurrentRole(res.data.current_role);
        setPermittedOrganisations(res.data.permitted_organisations);
        if (typeof window !== "undefined") {
          localStorage.setItem("brandcanon_active_org_id", res.data.active_organisation.id);
        }
      } else {
        setUser(null);
        setActiveOrganisation(null);
        setCurrentRole(null);
        setPermittedOrganisations([]);
        if (typeof window !== "undefined") {
          localStorage.removeItem("brandcanon_token");
          localStorage.removeItem("brandcanon_active_org_id");
        }
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("brandcanon_token") : null;
    if (token) {
      refreshMe();
    } else {
      setIsLoading(false);
    }
  }, [refreshMe]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    const res = await api.auth.login({ email, password });
    if (res.success && res.data) {
      if (typeof window !== "undefined") {
        localStorage.setItem("brandcanon_token", res.data.access_token);
        localStorage.setItem("brandcanon_active_org_id", res.data.active_organisation.id);
      }
      setUser(res.data.user);
      setActiveOrganisation(res.data.active_organisation);
      setCurrentRole(res.data.current_role);
      await refreshMe();
      setIsLoading(false);
      return { success: true };
    }
    setIsLoading(false);
    return { success: false, error: res.error?.message || "Login failed" };
  };

  const register = async (payload: {
    email: string;
    password: string;
    full_name: string;
    organisation_name?: string;
  }) => {
    setIsLoading(true);
    const res = await api.auth.register(payload);
    if (res.success && res.data) {
      if (typeof window !== "undefined") {
        localStorage.setItem("brandcanon_token", res.data.access_token);
        localStorage.setItem("brandcanon_active_org_id", res.data.active_organisation.id);
      }
      setUser(res.data.user);
      setActiveOrganisation(res.data.active_organisation);
      setCurrentRole(res.data.current_role);
      await refreshMe();
      setIsLoading(false);
      return { success: true };
    }
    setIsLoading(false);
    return { success: false, error: res.error?.message || "Registration failed" };
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // Ignore network errors on logout
    }
    if (typeof window !== "undefined") {
      localStorage.removeItem("brandcanon_token");
      localStorage.removeItem("brandcanon_active_org_id");
    }
    setUser(null);
    setActiveOrganisation(null);
    setCurrentRole(null);
    setPermittedOrganisations([]);
  };

  const switchOrganisation = async (orgId: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("brandcanon_active_org_id", orgId);
    }
    setIsLoading(true);
    await refreshMe();
  };

  const isAdmin = currentRole === "ADMIN";
  const isBrandManager = currentRole === "BRAND_MANAGER";
  const isCreator = currentRole === "CREATOR";
  const isReviewer = currentRole === "REVIEWER";

  const hasPermission = (allowedRoles: RoleType[]) => {
    if (!currentRole) return false;
    return allowedRoles.includes(currentRole);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeOrganisation,
        currentRole,
        permittedOrganisations,
        isLoading,
        isAuthenticated: !!user,
        isAdmin,
        isBrandManager,
        isCreator,
        isReviewer,
        hasPermission,
        login,
        register,
        logout,
        switchOrganisation,
        refreshMe,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

