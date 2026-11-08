export interface SubmissionListItem {
  id: string;
  title: string;
  content_type: string;
  current_status: string;
  publishing_channel: string;
  campaign_name?: string | null;
  target_audience?: string | null;
  intended_publication_date?: string | null;
  created_at: string;
  updated_at: string;
  latest_review_status?: string | null;
}

export interface ContentVersionDetail {
  id: string;
  version_number: number;
  content_text: string;
  content_hash: string;
  word_count: number;
  character_count: number;
  created_at: string;
}

export interface SuggestionDetail {
  id: string;
  finding_id: string;
  original_text: string;
  suggested_text: string;
  reason: string;
  status: string;
  created_at: string;
}

export interface EvidenceDetail {
  id: string;
  finding_id: string;
  document_id: string;
  document_version_id: string;
  chunk_id: string;
  source_quote: string;
  source_page?: number | null;
  source_location?: string | null;
  relevance_metadata: Record<string, any>;
  verification_status: string;
  created_at: string;
}

export interface FindingDetail {
  id: string;
  category: string;
  status: string;
  severity: string;
  confidence_level: string;
  original_text: string;
  start_offset: number;
  end_offset: number;
  explanation?: string | null;
  suggestion?: SuggestionDetail | null;
  evidences: EvidenceDetail[];
  created_at: string;
}

export interface ReviewResultDetail {
  id: string;
  overall_status: string;
  findings_count: number;
  model_provider?: string | null;
  model_identifier?: string | null;
  findings: FindingDetail[];
  created_at: string;
}

export interface SubmissionDetail {
  id: string;
  organisation_id: string;
  creator_id?: string | null;
  title: string;
  content_type: string;
  publishing_channel: string;
  campaign_name?: string | null;
  target_audience?: string | null;
  applicable_region: string;
  language: string;
  description?: string | null;
  current_status: string;
  current_version_number: number;
  created_at: string;
  updated_at: string;
  versions: ContentVersionDetail[];
  latest_review_result?: ReviewResultDetail | null;
}

export interface CreateSubmissionInput {
  title: string;
  content_type?: string;
  publishing_channel?: string;
  campaign_name?: string;
  target_audience?: string;
  applicable_region?: string;
  language?: string;
  description?: string;
  content_text: string;
}

