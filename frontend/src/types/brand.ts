export interface BrandProfile {
  id: string;
  organisation_id: string;
  brand_name: string;
  industry?: string | null;
  domain?: string | null;
  description?: string | null;
  brand_voice?: string | null;
  target_audience?: string | null;
  publishing_channels: string[];
  applicable_regions: string[];
  created_at: string;
  updated_at: string;
}

export interface DocumentVersion {
  id: string;
  version_number: number;
  content_hash: string;
  extraction_status: string;
  total_pages: number;
  total_chunks: number;
  created_at: string;
}

export interface BrandDocument {
  id: string;
  organisation_id: string;
  document_name: string;
  file_type: "docx" | "pdf" | string;
  file_size: number;
  current_version: number;
  processing_status: "UPLOADED" | "PROCESSING" | "EXTRACTED" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "ARCHIVED" | "FAILED" | "UNSUPPORTED_SCANNED_DOCUMENT" | string;
  approval_status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "ARCHIVED" | string;
  uploaded_by?: string | null;
  created_at: string;
  updated_at: string;
  versions?: DocumentVersion[];
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  source_page?: number | null;
  source_location?: string | null;
  content_hash: string;
}

export interface DocumentContent {
  document_id: string;
  document_name: string;
  extraction_status: string;
  total_pages: number;
  total_chunks: number;
  text_preview: string;
  chunks: DocumentChunk[];
}

export interface ApprovedFact {
  id: string;
  organisation_id: string;
  brand_document_id?: string | null;
  title: string;
  claim_text: string;
  category: string;
  evidence_quote?: string | null;
  source_page?: number | null;
  source_location?: string | null;
  applicable_region: string;
  applicable_audience: string;
  valid_from?: string | null;
  valid_until?: string | null;
  status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "ARCHIVED" | string;
  created_by?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TerminologyRule {
  id: string;
  organisation_id: string;
  preferred_term: string;
  prohibited_term: string;
  description?: string | null;
  match_type: "EXACT" | "WHOLE_WORD" | "PHRASE" | string;
  case_sensitive: boolean;
  category: string;
  severity: "HIGH" | "MEDIUM" | "LOW" | string;
  applicable_channel: string;
  applicable_region: string;
  status: "ACTIVE" | "PENDING_APPROVAL" | "REJECTED" | "ARCHIVED" | string;
  source_document_id?: string | null;
  created_by?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TerminologyMatch {
  rule_id: string;
  prohibited_term: string;
  preferred_term: string;
  match_start: number;
  match_end: number;
  matched_text: string;
  severity: string;
  category: string;
  match_type: string;
  description?: string | null;
}

export interface KnowledgeApproval {
  id: string;
  organisation_id: string;
  entity_type: "DOCUMENT" | "FACT" | "TERMINOLOGY_RULE" | string;
  entity_id: string;
  decision: "APPROVED" | "REJECTED" | "ARCHIVED" | string;
  reviewer_id: string;
  reason?: string | null;
  created_at: string;
}

export interface KnowledgeOverviewStats {
  total_documents: number;
  approved_documents: number;
  pending_documents: number;
  total_facts: number;
  approved_facts: number;
  pending_facts: number;
  total_terminology_rules: number;
  active_terminology_rules: number;
  pending_terminology_rules: number;
  total_chunks: number;
}

