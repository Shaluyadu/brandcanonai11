import { RoleType } from "./auth";

export interface Member {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: RoleType;
  is_default: boolean;
  created_at: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
