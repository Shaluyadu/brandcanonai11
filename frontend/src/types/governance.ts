import { APIResponse } from "@/types/auth";
import { SubmissionListItem } from "@/types/submission";

export interface DashboardStats {
  total_submissions: number;
  pending_reviews: number;
  in_review: number;
  changes_requested: number;
  approved: number;
  rejected: number;
  review_incomplete: number;
  high_risk_findings: number;
}

export interface SubmissionsResponse {
  items: SubmissionListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GovernanceAPI {
  getDashboard: () => Promise<APIResponse<DashboardStats>>;
  getSubmissions: (params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
    channel?: string;
    author?: string;
    startDate?: string;
    endDate?: string;
    sortBy?: string;
    sortOrder?: string;
  }) => Promise<APIResponse<SubmissionsResponse>>;
}
