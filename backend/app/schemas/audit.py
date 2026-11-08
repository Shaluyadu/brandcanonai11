from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AuditLogOut(BaseModel):
    id: str
    organisation_id: str
    user_id: Optional[str] = None
    event_type: str
    entity_type: str
    entity_id: str
    metadata_json: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
