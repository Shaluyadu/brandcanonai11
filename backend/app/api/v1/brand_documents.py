"""
Brand Documents API endpoints.
Handles upload, parsing, versioning, chunk viewing, and approval lifecycle for brand documents.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.api.deps import (
    get_current_user,
    get_current_tenant,
    require_role,
    record_audit_log
)
from app.models.user import User, Membership, RoleEnum
from app.models.organisation import Organisation
from app.models.brand_knowledge import (
    BrandDocument,
    DocumentVersion,
    DocumentChunk,
    KnowledgeApproval,
    DocumentProcessingStatus,
    ApprovalStatus
)
from app.models.base import utc_now, generate_uuid
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.brand_knowledge import (
    DocumentOut,
    DocumentDetailOut,
    DocumentVersionOut,
    DocumentContentOut,
    ChunkOut,
    ApprovalDecisionRequest
)
from app.ingestion.file_validator import validate_upload_file
from app.ingestion.storage import storage_service
from app.ingestion.ingestion_service import process_document

router = APIRouter()


@router.post("/documents", response_model=APIResponse[DocumentDetailOut], status_code=status.HTTP_201_CREATED)
async def upload_brand_document(
    file: UploadFile = File(...),
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """
    Upload a brand guidelines or specifications document (DOCX or PDF, max 25MB).
    Validates magic bytes, saves to private storage, extracts text & creates chunks.
    """
    raw_content = await file.read()
    filename = file.filename or "uploaded_document"

    # Validate file type, magic bytes, size limit
    validation = validate_upload_file(raw_content, filename)

    # Save to tenant-isolated private storage
    storage_key = storage_service.save_file(
        organisation_id=tenant.id,
        content=raw_content,
        file_ext=validation.file_type
    )

    # Create BrandDocument record
    doc = BrandDocument(
        id=generate_uuid(),
        organisation_id=tenant.id,
        uploaded_by=current_user.id,
        document_name=validation.sanitized_name,
        storage_key=storage_key,
        file_type=validation.file_type,
        file_size=validation.file_size,
        current_version=1,
        processing_status=DocumentProcessingStatus.UPLOADED.value,
        approval_status=ApprovalStatus.PENDING_APPROVAL.value
    )
    db.add(doc)
    db.flush()

    # Create initial DocumentVersion
    doc_version = DocumentVersion(
        id=generate_uuid(),
        organisation_id=tenant.id,
        document_id=doc.id,
        version_number=1,
        content_hash=validation.content_hash,
        extraction_status="PENDING",
        total_pages=1,
        total_chunks=0
    )
    db.add(doc_version)
    db.flush()

    # Process document synchronously (extract, normalize, chunk)
    try:
        process_document(
            document_id=doc.id,
            organisation_id=tenant.id,
            db=db,
            storage=storage_service
        )
    except Exception as exc:
        # Processing failed but document record is retained with FAILED status
        db.flush()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="DOCUMENT_UPLOADED",
        entity_type="BRAND_DOCUMENT",
        entity_id=doc.id,
        metadata={
            "document_name": doc.document_name,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "content_hash": validation.content_hash,
            "processing_status": doc.processing_status
        }
    )
    db.commit()
    db.refresh(doc)

    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).all()
    out = DocumentDetailOut(
        id=doc.id,
        organisation_id=doc.organisation_id,
        document_name=doc.document_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        current_version=doc.current_version,
        processing_status=doc.processing_status,
        approval_status=doc.approval_status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        versions=[DocumentVersionOut.model_validate(v) for v in versions]
    )

    return APIResponse(
        success=True,
        message="Document uploaded and processed successfully",
        data=out
    )


@router.get("/documents", response_model=APIResponse[PaginatedResponse[DocumentOut]])
def list_brand_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    processing_status: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """List brand documents in the workspace with pagination and filters."""
    query = db.query(BrandDocument).filter(BrandDocument.organisation_id == tenant.id)

    if processing_status:
        query = query.filter(BrandDocument.processing_status == processing_status)
    if approval_status:
        query = query.filter(BrandDocument.approval_status == approval_status)

    total = query.count()
    items = query.order_by(BrandDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    docs_out = [DocumentOut.model_validate(d) for d in items]

    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=docs_out,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/documents/{document_id}", response_model=APIResponse[DocumentDetailOut])
def get_brand_document(
    document_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Get document details including version history."""
    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).order_by(DocumentVersion.version_number.desc()).all()

    out = DocumentDetailOut(
        id=doc.id,
        organisation_id=doc.organisation_id,
        document_name=doc.document_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        current_version=doc.current_version,
        processing_status=doc.processing_status,
        approval_status=doc.approval_status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        versions=[DocumentVersionOut.model_validate(v) for v in versions]
    )

    return APIResponse(success=True, data=out)


@router.get("/documents/{document_id}/content", response_model=APIResponse[DocumentContentOut])
def get_document_content(
    document_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Preview extracted text and individual chunks for a document."""
    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == doc.id,
        DocumentVersion.version_number == doc.current_version
    ).first()

    if not version:
        raise NotFoundError("Document version not found")

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_version_id == version.id
    ).order_by(DocumentChunk.chunk_index.asc()).all()

    text_preview = (version.extracted_text or "")[:5000]

    out = DocumentContentOut(
        document_id=doc.id,
        document_name=doc.document_name,
        extraction_status=version.extraction_status,
        total_pages=version.total_pages,
        total_chunks=len(chunks),
        text_preview=text_preview,
        chunks=[ChunkOut.model_validate(c) for c in chunks]
    )

    return APIResponse(success=True, data=out)


@router.post("/documents/{document_id}/process", response_model=APIResponse[DocumentDetailOut])
def reprocess_document(
    document_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Re-trigger parsing and chunking for a document."""
    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    process_document(
        document_id=doc.id,
        organisation_id=tenant.id,
        db=db,
        storage=storage_service
    )

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="DOCUMENT_REPROCESSED",
        entity_type="BRAND_DOCUMENT",
        entity_id=doc.id,
        metadata={"processing_status": doc.processing_status}
    )
    db.commit()
    db.refresh(doc)

    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).all()
    out = DocumentDetailOut(
        id=doc.id,
        organisation_id=doc.organisation_id,
        document_name=doc.document_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        current_version=doc.current_version,
        processing_status=doc.processing_status,
        approval_status=doc.approval_status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        versions=[DocumentVersionOut.model_validate(v) for v in versions]
    )

    return APIResponse(
        success=True,
        message="Document reprocessed successfully",
        data=out
    )


@router.post("/documents/{document_id}/approve", response_model=APIResponse[DocumentDetailOut])
def approve_document(
    document_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Approve a document to activate it for the organisation's knowledge hub."""
    if payload.decision != "APPROVED":
        raise ValidationError("Decision must be 'APPROVED' for this endpoint")

    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    doc.approval_status = ApprovalStatus.APPROVED.value

    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == doc.id,
        DocumentVersion.version_number == doc.current_version
    ).first()

    now = utc_now()
    if version:
        version.approved_by = current_user.id
        version.approved_at = now

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        decision="APPROVED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="DOCUMENT_APPROVED",
        entity_type="BRAND_DOCUMENT",
        entity_id=doc.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(doc)

    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).all()
    out = DocumentDetailOut(
        id=doc.id,
        organisation_id=doc.organisation_id,
        document_name=doc.document_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        current_version=doc.current_version,
        processing_status=doc.processing_status,
        approval_status=doc.approval_status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        versions=[DocumentVersionOut.model_validate(v) for v in versions]
    )

    return APIResponse(
        success=True,
        message="Document approved successfully",
        data=out
    )


@router.post("/documents/{document_id}/reject", response_model=APIResponse[DocumentDetailOut])
def reject_document(
    document_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Reject a document (excluded from active knowledge)."""
    if payload.decision != "REJECTED":
        raise ValidationError("Decision must be 'REJECTED' for this endpoint")

    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    doc.approval_status = ApprovalStatus.REJECTED.value

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        decision="REJECTED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="DOCUMENT_REJECTED",
        entity_type="BRAND_DOCUMENT",
        entity_id=doc.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(doc)

    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).all()
    out = DocumentDetailOut(
        id=doc.id,
        organisation_id=doc.organisation_id,
        document_name=doc.document_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        current_version=doc.current_version,
        processing_status=doc.processing_status,
        approval_status=doc.approval_status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        versions=[DocumentVersionOut.model_validate(v) for v in versions]
    )

    return APIResponse(
        success=True,
        message="Document rejected",
        data=out
    )


@router.post("/documents/{document_id}/archive", response_model=APIResponse[DocumentDetailOut])
def archive_document(
    document_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Archive a document (retired from active knowledge)."""
    if payload.decision != "ARCHIVED":
        raise ValidationError("Decision must be 'ARCHIVED' for this endpoint")

    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    doc.approval_status = ApprovalStatus.ARCHIVED.value

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        decision="ARCHIVED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="DOCUMENT_ARCHIVED",
        entity_type="BRAND_DOCUMENT",
        entity_id=doc.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(doc)

    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).all()
    out = DocumentDetailOut(
        id=doc.id,
        organisation_id=doc.organisation_id,
        document_name=doc.document_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        current_version=doc.current_version,
        processing_status=doc.processing_status,
        approval_status=doc.approval_status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        versions=[DocumentVersionOut.model_validate(v) for v in versions]
    )

    return APIResponse(
        success=True,
        message="Document archived",
        data=out
    )


@router.delete("/documents/{document_id}", response_model=APIResponse[dict])
def delete_document(
    document_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Delete a document and its stored file."""
    doc = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == tenant.id
    ).first()

    if not doc:
        raise NotFoundError("Document not found in workspace")

    # Delete from private storage
    try:
        storage_service.delete_file(tenant.id, doc.storage_key)
    except Exception:
        pass

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="DOCUMENT_DELETED",
        entity_type="BRAND_DOCUMENT",
        entity_id=doc.id,
        metadata={"document_name": doc.document_name}
    )

    db.delete(doc)
    db.commit()

    return APIResponse(
        success=True,
        message="Document deleted successfully",
        data={"document_id": document_id}
    )

