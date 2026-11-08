export interface AuditLog {
  id: string;
  organisation_id: string;
  user_id?: string | null;
  event_type: string;
  entity_type: string;
  entity_id: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

