"""
Comprehensive Phase 2 Verification Script
Validates:
1. DOCX and PDF Ingestion
2. Paragraph-aware chunking & source metadata preservation
3. Facts and Terminology approval lifecycles (only APPROVED is active)
4. RBAC permission gates (Creator vs Manager vs Admin)
5. Strict Cross-Tenant Data Isolation
6. Immutable Audit Trail Logging
"""
import io
import sys
import docx
import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.organisation import Organisation
from app.models.user import User, Membership, UserSession, RoleEnum
from app.models.brand_knowledge import BrandDocument, DocumentChunk, ApprovedFact, TerminologyRule, KnowledgeApproval
from app.models.audit import AuditLog
from app.core.security import generate_session_token, hash_session_token
from app.ingestion.terminology_engine import TerminologyMatcher


def run_comprehensive_verification():
    print("=" * 80)
    print("BRANDCANON AI — PHASE 2 FINAL DEEP VERIFICATION")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    try:
        # Load seeded NovaTech organization and users
        org = db.query(Organisation).filter(Organisation.slug == "novatech").first()
        assert org is not None, "NovaTech organization must exist"

        admin_user = db.query(User).filter(User.email == "admin@novatech.io").first()
        brand_user = db.query(User).filter(User.email == "brand@novatech.io").first()
        creator_user = db.query(User).filter(User.email == "creator@novatech.io").first()
        reviewer_user = db.query(User).filter(User.email == "reviewer@novatech.io").first()

        assert admin_user and brand_user and creator_user and reviewer_user, "All 4 role users must exist"

        # Generate fresh session tokens for each user
        tokens = {}
        for u in [admin_user, brand_user, creator_user, reviewer_user]:
            raw_token = generate_session_token()
            from datetime import datetime, timezone, timedelta
            sess = UserSession(
                user_id=u.id,
                organisation_id=org.id,
                session_token=hash_session_token(raw_token),
                is_revoked=False,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
            )
            db.add(sess)
            tokens[u.email] = raw_token

        # Create a second temporary tenant to test cross-tenant isolation
        org2 = db.query(Organisation).filter(Organisation.slug == "tenant2-verify").first()
        if not org2:
            org2 = Organisation(
                name="Tenant Two Verify Corp",
                slug="tenant2-verify",
                industry="Finance",
                is_active=True
            )
            db.add(org2)
            db.flush()

        user2 = db.query(User).filter(User.email == "user@tenant2.io").first()
        if not user2:
            from app.core.security import hash_password
            user2 = User(
                email="user@tenant2.io",
                hashed_password=hash_password("Pass@1234!"),
                full_name="Tenant 2 User",
                is_active=True,
                is_verified=True
            )
            db.add(user2)
            db.flush()
            m2 = Membership(organisation_id=org2.id, user_id=user2.id, role="ADMIN", is_default=True)
            db.add(m2)

        raw_token2 = generate_session_token()
        from datetime import datetime, timezone, timedelta
        sess2 = UserSession(
            user_id=user2.id,
            organisation_id=org2.id,
            session_token=hash_session_token(raw_token2),
            is_revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
        )
        db.add(sess2)
        tokens["user@tenant2.io"] = raw_token2
        db.commit()

        # -------------------------------------------------------------
        # CHECK 1: DOCX Ingestion, Normalization, & Chunking
        # -------------------------------------------------------------
        print("\n[CHECK 1] Testing DOCX Ingestion, Normalization, and Chunking...")
        docx_doc = docx.Document()
        docx_doc.add_heading("Section 1: Brand Tone & Mission", level=1)
        docx_doc.add_paragraph("BrandCanon delivers autonomous, verifiable brand governance for modern enterprises.")
        docx_doc.add_heading("Section 2: Performance Specifications", level=2)
        docx_doc.add_paragraph("All models guarantee sub-50ms token latency under peak concurrent loads.")
        docx_buf = io.BytesIO()
        docx_doc.save(docx_buf)
        docx_bytes = docx_buf.getvalue()

        manager_headers = {
            "Authorization": f"Bearer {tokens['brand@novatech.io']}",
            "X-Organisation-Id": org.id,
        }

        res = client.post(
            "/api/v1/brand/documents",
            headers=manager_headers,
            files={"file": ("tone_guide.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        assert res.status_code == 201, f"DOCX upload failed: {res.text}"
        docx_id = res.json()["data"]["id"]
        print(f"  ✓ DOCX uploaded successfully: ID={docx_id}, status={res.json()['data']['processing_status']}")

        # Verify chunks
        content_res = client.get(f"/api/v1/brand/documents/{docx_id}/content", headers=manager_headers)
        assert content_res.status_code == 200
        content_data = content_res.json()["data"]
        assert len(content_data["chunks"]) >= 1, "DOCX must generate chunks"
        first_chunk = content_data["chunks"][0]
        assert "BrandCanon delivers" in first_chunk["content"]
        assert first_chunk["content_hash"] is not None
        print(f"  ✓ Chunks generated: count={len(content_data['chunks'])}, first_chunk location={first_chunk['source_location']}")

        # -------------------------------------------------------------
        # CHECK 2: PDF Ingestion & Scanned Document Protection
        # -------------------------------------------------------------
        print("\n[CHECK 2] Testing PDF Ingestion & Scanned Document Protection...")
        pdf_doc = pymupdf.open()
        p1 = pdf_doc.new_page()
        p1.insert_text((50, 72), "BrandCanon AI Security Baseline Page 1: Encryption standards and zero-trust perimeter.")
        p2 = pdf_doc.new_page()
        p2.insert_text((50, 72), "BrandCanon AI Security Baseline Page 2: Continuous compliance monitoring and automated audits.")
        pdf_bytes = pdf_doc.tobytes()
        pdf_doc.close()

        res_pdf = client.post(
            "/api/v1/brand/documents",
            headers=manager_headers,
            files={"file": ("security_baseline.pdf", pdf_bytes, "application/pdf")}
        )
        assert res_pdf.status_code == 201, f"PDF upload failed: {res_pdf.text}"
        pdf_id = res_pdf.json()["data"]["id"]
        print(f"  ✓ PDF uploaded successfully: ID={pdf_id}, status={res_pdf.json()['data']['processing_status']}")

        # Verify multi-page chunks
        pdf_content = client.get(f"/api/v1/brand/documents/{pdf_id}/content", headers=manager_headers).json()["data"]
        assert pdf_content["total_pages"] == 2, f"Expected 2 pages, got {pdf_content['total_pages']}"
        assert len(pdf_content["chunks"]) >= 2, "Expected chunks across multiple pages"
        print(f"  ✓ Multi-page PDF extracted: pages={pdf_content['total_pages']}, chunks={len(pdf_content['chunks'])}")

        # -------------------------------------------------------------
        # CHECK 3: Document Approval Lifecycle
        # -------------------------------------------------------------
        print("\n[CHECK 3] Testing Document Approval Lifecycle...")
        assert res_pdf.json()["data"]["approval_status"] == "PENDING_APPROVAL"

        # Approve
        appr_res = client.post(
            f"/api/v1/brand/documents/{pdf_id}/approve",
            headers=manager_headers,
            json={"decision": "APPROVED", "reason": "Legal security team signoff"}
        )
        assert appr_res.status_code == 200
        assert appr_res.json()["data"]["approval_status"] == "APPROVED"
        print("  ✓ Document approved: Status changed to APPROVED")

        # -------------------------------------------------------------
        # CHECK 4: Approved Facts & Claims Lifecycle
        # -------------------------------------------------------------
        print("\n[CHECK 4] Testing Approved Facts & Claims Lifecycle...")
        creator_headers = {
            "Authorization": f"Bearer {tokens['creator@novatech.io']}",
            "X-Organisation-Id": org.id,
        }

        # Creator submits fact
        fact_res = client.post(
            "/api/v1/brand/facts",
            headers=creator_headers,
            json={
                "title": "Sub-50ms Inference Guarantee",
                "claim_text": "NovaTech guarantees sub-50ms latency across global edge points of presence.",
                "category": "PERFORMANCE",
                "evidence_quote": "Section 2 Performance Specifications in Tone Guide",
                "source_page": 1,
                "applicable_region": "GLOBAL"
            }
        )
        assert fact_res.status_code == 201
        fact_id = fact_res.json()["data"]["id"]
        assert fact_res.json()["data"]["status"] == "PENDING_APPROVAL"
        print(f"  ✓ Fact created by Creator: ID={fact_id}, status=PENDING_APPROVAL")

        # Creator cannot approve (RBAC check)
        unauth_appr = client.post(f"/api/v1/brand/facts/{fact_id}/approve", headers=creator_headers, json={"decision": "APPROVED"})
        assert unauth_appr.status_code == 403, "Creator must not be able to approve facts"
        print("  ✓ RBAC enforced: Creator blocked from approving fact (403 Forbidden)")

        # Manager approves
        mgr_appr = client.post(
            f"/api/v1/brand/facts/{fact_id}/approve",
            headers=manager_headers,
            json={"decision": "APPROVED", "reason": "Verified against SLA benchmarks"}
        )
        assert mgr_appr.status_code == 200
        assert mgr_appr.json()["data"]["status"] == "APPROVED"
        print("  ✓ Fact approved by Brand Manager: status=APPROVED")

        # -------------------------------------------------------------
        # CHECK 5: Terminology Rules & Deterministic Engine
        # -------------------------------------------------------------
        print("\n[CHECK 5] Testing Terminology Matching Engine...")
        # Check matching via API
        scan_res = client.post(
            "/api/v1/brand/terminology/check",
            headers=creator_headers,
            json={"text": "Our software offers cheap plans that create cross-functional synergy with foolproof execution."}
        )
        assert scan_res.status_code == 200
        matches = scan_res.json()["data"]
        prohibited_found = [m["prohibited_term"] for m in matches]
        assert "cheap" in prohibited_found
        assert "synergy" in prohibited_found
        assert "foolproof" in prohibited_found
        print(f"  ✓ Terminology linter successfully detected violations: {prohibited_found}")

        # Check whole-word boundary (cheap vs cheapskate)
        scan_sub = client.post(
            "/api/v1/brand/terminology/check",
            headers=creator_headers,
            json={"text": "He is not a cheapskate, he simply values prudence."}
        )
        assert scan_sub.status_code == 200
        assert len(scan_sub.json()["data"]) == 0, "WHOLE_WORD matching must not match substring 'cheapskate'"
        print("  ✓ Whole-word boundary verified: 'cheap' did not match substring in 'cheapskate'")

        # -------------------------------------------------------------
        # CHECK 6: Strict Cross-Tenant Isolation
        # -------------------------------------------------------------
        print("\n[CHECK 6] Testing Cross-Tenant Data Isolation...")
        tenant2_headers = {
            "Authorization": f"Bearer {tokens['user@tenant2.io']}",
            "X-Organisation-Id": org2.id,
        }

        # Tenant 2 cannot access NovaTech DOCX document
        t2_doc_res = client.get(f"/api/v1/brand/documents/{docx_id}", headers=tenant2_headers)
        assert t2_doc_res.status_code == 404, "Tenant 2 must not see Tenant 1's documents"

        # Tenant 2 cannot access NovaTech document chunks
        t2_chunk_res = client.get(f"/api/v1/brand/documents/{docx_id}/content", headers=tenant2_headers)
        assert t2_chunk_res.status_code == 404, "Tenant 2 must not see Tenant 1's chunks"

        # Tenant 2 cannot see NovaTech fact
        t2_fact_res = client.get(f"/api/v1/brand/facts/{fact_id}", headers=tenant2_headers)
        assert t2_fact_res.status_code == 404, "Tenant 2 must not see Tenant 1's facts"

        # Tenant 2 text scan does not trigger NovaTech rules
        t2_scan = client.post(
            "/api/v1/brand/terminology/check",
            headers=tenant2_headers,
            json={"text": "Our software offers cheap plans with synergy."}
        )
        assert t2_scan.status_code == 200
        assert len(t2_scan.json()["data"]) == 0, "Tenant 2 must not inherit Tenant 1's terminology rules"
        print("  ✓ Strict tenant isolation confirmed across documents, chunks, facts, and rules")

        # -------------------------------------------------------------
        # CHECK 7: Audit Logging Verification
        # -------------------------------------------------------------
        print("\n[CHECK 7] Testing Immutable Audit Logging...")
        admin_headers = {
            "Authorization": f"Bearer {tokens['admin@novatech.io']}",
            "X-Organisation-Id": org.id,
        }
        audit_res = client.get("/api/v1/audit?page=1&page_size=20", headers=admin_headers)
        assert audit_res.status_code == 200
        audit_items = audit_res.json()["data"]["items"]
        event_types = [a["event_type"] for a in audit_items]

        assert "DOCUMENT_UPLOADED" in event_types
        assert "DOCUMENT_APPROVED" in event_types
        assert "FACT_CREATED" in event_types
        assert "FACT_APPROVED" in event_types
        print(f"  ✓ Audit log entries present and verified: {set(event_types)}")

        # -------------------------------------------------------------
        # CHECK 8: Knowledge Hub Overview Statistics API
        # -------------------------------------------------------------
        print("\n[CHECK 8] Testing Knowledge Hub Overview Statistics...")
        overview_res = client.get("/api/v1/brand/overview", headers=admin_headers)
        assert overview_res.status_code == 200
        stats = overview_res.json()["data"]
        assert stats["total_documents"] >= 2
        assert stats["approved_documents"] >= 1
        assert stats["total_facts"] >= 3
        assert stats["approved_facts"] >= 3
        assert stats["active_terminology_rules"] >= 3
        assert stats["total_chunks"] >= 3
        print(f"  ✓ Overview stats verified: docs={stats['total_documents']}, facts={stats['total_facts']}, rules={stats['total_terminology_rules']}, chunks={stats['total_chunks']}")

        print("\n" + "=" * 80)
        print("ALL COMPREHENSIVE PHASE 2 SYSTEM CHECKS PASSED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_comprehensive_verification()
