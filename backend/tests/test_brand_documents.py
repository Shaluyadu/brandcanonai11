"""
Automated tests for Brand Documents API, ingestion, chunking, and tenant isolation.
"""
import io
import docx
import pymupdf
import pytest


def create_sample_docx(text: str = "BrandCanon Voice and Tone Guidelines. Always be helpful and accurate.") -> bytes:
    doc = docx.Document()
    doc.add_heading("Brand Identity", level=1)
    doc.add_paragraph(text)
    doc.add_paragraph("Approved Claims: 99.9% uptime guaranteed across all regions.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_sample_pdf(text: str = "BrandCanon Official Style Guide. Innovation meets compliance.") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    page.insert_text((50, 100), "Section 2: Preferred terminology and disallowed promotional superlatives.")
    bytes_data = doc.tobytes()
    doc.close()
    return bytes_data


def test_upload_valid_docx(client, test_data):
    """Brand Manager uploads a valid DOCX document."""
    docx_bytes = create_sample_docx()
    headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    files = {
        "file": ("guidelines.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

    response = client.post("/api/v1/brand/documents", headers=headers, files=files)
    assert response.status_code == 201
    data = response.json()["data"]

    assert data["document_name"] == "guidelines.docx"
    assert data["file_type"] == "docx"
    assert data["processing_status"] in ["EXTRACTED", "UPLOADED"]
    assert data["approval_status"] == "PENDING_APPROVAL"
    assert len(data["versions"]) >= 1

    doc_id = data["id"]

    # Verify content extraction and chunks
    content_res = client.get(f"/api/v1/brand/documents/{doc_id}/content", headers=headers)
    assert content_res.status_code == 200
    c_data = content_res.json()["data"]
    assert c_data["extraction_status"] == "EXTRACTED"
    assert "BrandCanon Voice and Tone Guidelines" in c_data["text_preview"]
    assert len(c_data["chunks"]) >= 1


def test_upload_valid_pdf(client, test_data):
    """Admin uploads a valid PDF document."""
    pdf_bytes = create_sample_pdf()
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    files = {
        "file": ("style_guide.pdf", pdf_bytes, "application/pdf")
    }

    response = client.post("/api/v1/brand/documents", headers=headers, files=files)
    assert response.status_code == 201
    data = response.json()["data"]

    assert data["document_name"] == "style_guide.pdf"
    assert data["file_type"] == "pdf"
    assert data["processing_status"] in ["EXTRACTED", "UPLOADED"]

    # Content preview
    content_res = client.get(f"/api/v1/brand/documents/{data['id']}/content", headers=headers)
    assert content_res.status_code == 200
    c_data = content_res.json()["data"]
    assert c_data["total_pages"] >= 1
    assert "BrandCanon Official Style Guide" in c_data["text_preview"]


def test_upload_invalid_file_format(client, test_data):
    """Disallow unsupported extensions like .txt."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    files = {
        "file": ("notes.txt", b"Plain text notes", "text/plain")
    }

    response = client.post("/api/v1/brand/documents", headers=headers, files=files)
    assert response.status_code == 422


def test_upload_corrupted_file(client, test_data):
    """Disallow file with .pdf extension but invalid magic bytes."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    files = {
        "file": ("fake.pdf", b"NOT A REAL PDF CONTENT", "application/pdf")
    }

    response = client.post("/api/v1/brand/documents", headers=headers, files=files)
    assert response.status_code == 422


def test_creator_cannot_upload_document(client, test_data):
    """Creator role lacks permission to upload brand documents."""
    docx_bytes = create_sample_docx()
    headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    files = {
        "file": ("guidelines.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

    response = client.post("/api/v1/brand/documents", headers=headers, files=files)
    assert response.status_code == 403


def test_document_approval_lifecycle(client, test_data):
    """Document approval, rejection, and archival workflow."""
    pdf_bytes = create_sample_pdf()
    admin_headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    # Upload
    files = {"file": ("lifecycle.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/v1/brand/documents", headers=admin_headers, files=files)
    assert res.status_code == 201
    doc_id = res.json()["data"]["id"]

    # Approve
    approve_res = client.post(
        f"/api/v1/brand/documents/{doc_id}/approve",
        headers=admin_headers,
        json={"decision": "APPROVED", "reason": "Verified against legal standards"}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["approval_status"] == "APPROVED"

    # Reject
    reject_res = client.post(
        f"/api/v1/brand/documents/{doc_id}/reject",
        headers=admin_headers,
        json={"decision": "REJECTED", "reason": "Outdated product specs"}
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["approval_status"] == "REJECTED"

    # Archive
    archive_res = client.post(
        f"/api/v1/brand/documents/{doc_id}/archive",
        headers=admin_headers,
        json={"decision": "ARCHIVED", "reason": "Replaced by Q4 edition"}
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["data"]["approval_status"] == "ARCHIVED"


def test_tenant_isolation_documents(client, test_data):
    """Tenant 2 user cannot access Tenant 1's documents."""
    docx_bytes = create_sample_docx()
    org1_headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }
    org2_headers = {
        "Authorization": f"Bearer {test_data['org2_token']}",
        "X-Organisation-Id": test_data["org2"].id,
    }

    # Org 1 uploads document
    files = {"file": ("secret.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/brand/documents", headers=org1_headers, files=files)
    assert res.status_code == 201
    doc_id = res.json()["data"]["id"]

    # Org 2 attempts to get Org 1's document
    res_forbidden = client.get(f"/api/v1/brand/documents/{doc_id}", headers=org2_headers)
    assert res_forbidden.status_code == 404

    # Org 2 attempts to get Org 1's document content
    res_content_forbidden = client.get(f"/api/v1/brand/documents/{doc_id}/content", headers=org2_headers)
    assert res_content_forbidden.status_code == 404

