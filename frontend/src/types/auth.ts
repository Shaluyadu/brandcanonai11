export type RoleType = "ADMIN" | "BRAND_MANAGER" | "CREATOR" | "REVIEWER";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Organisation {
  id: string;
  name: string;
  slug: string;
  industry?: string | null;
  domain?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganisationSettings {
  id: string;
  organisation_id: string;
  enforce_brand_voice: boolean;
  strict_mode: boolean;
  custom_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface OrganisationDetail extends Organisation {
  settings?: OrganisationSettings | null;
}

export interface AuthResponseData {
  access_token: string;
  token_type: string;
  user: User;
  active_organisation: Organisation;
  current_role: RoleType;
}

export interface MeResponseData {
  user: User;
  active_organisation: Organisation;
  current_role: RoleType;
  permitted_organisations: Organisation[];
}

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

