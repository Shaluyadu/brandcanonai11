"""Brand Knowledge Hub schema: profiles, documents, chunks, facts, terminology, approvals

Revision ID: 002_brand_knowledge
Revises: 001_initial
Create Date: 2026-11-04 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_brand_knowledge'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. brand_profiles
    op.create_table(
        'brand_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('brand_name', sa.String(length=255), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('brand_voice', sa.Text(), nullable=True),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('publishing_channels', sa.JSON(), nullable=False),
        sa.Column('applicable_regions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organisation_id')
    )
    op.create_index(op.f('ix_brand_profiles_organisation_id'), 'brand_profiles', ['organisation_id'], unique=True)

    # 2. brand_documents
    op.create_table(
        'brand_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), nullable=True),
        sa.Column('document_name', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('current_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='UPLOADED'),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brand_documents_organisation_id'), 'brand_documents', ['organisation_id'], unique=False)
    op.create_index(op.f('ix_brand_documents_uploaded_by'), 'brand_documents', ['uploaded_by'], unique=False)
    op.create_index(op.f('ix_brand_documents_processing_status'), 'brand_documents', ['processing_status'], unique=False)
    op.create_index(op.f('ix_brand_documents_approval_status'), 'brand_documents', ['approval_status'], unique=False)

    # 3. document_versions
    op.create_table(
        'document_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('extraction_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['brand_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'version_number', name='uq_doc_version')
    )
    op.create_index(op.f('ix_document_versions_organisation_id'), 'document_versions', ['organisation_id'], unique=False)
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_content_hash'), 'document_versions', ['content_hash'], unique=False)

    # 4. document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('document_version_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_location', sa.String(length=255), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['brand_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_organisation_id'), 'document_chunks', ['organisation_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_document_version_id'), 'document_chunks', ['document_version_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_content_hash'), 'document_chunks', ['content_hash'], unique=False)
    op.create_index('ix_chunks_org_doc_ver', 'document_chunks', ['organisation_id', 'document_id', 'document_version_id'], unique=False)

    # 5. approved_facts
    op.create_table(
        'approved_facts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('brand_document_id', sa.String(length=36), nullable=True),
        sa.Column('document_version_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='PRODUCT_SPECIFICATION'),
        sa.Column('evidence_quote', sa.Text(), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_location', sa.String(length=255), nullable=True),
        sa.Column('applicable_region', sa.String(length=100), nullable=False, server_default='GLOBAL'),
        sa.Column('applicable_audience', sa.String(length=100), nullable=False, server_default='ALL'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['brand_document_id'], ['brand_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approved_facts_organisation_id'), 'approved_facts', ['organisation_id'], unique=False)
    op.create_index(op.f('ix_approved_facts_brand_document_id'), 'approved_facts', ['brand_document_id'], unique=False)
    op.create_index(op.f('ix_approved_facts_category'), 'approved_facts', ['category'], unique=False)
    op.create_index(op.f('ix_approved_facts_status'), 'approved_facts', ['status'], unique=False)

    # 6. terminology_rules
    op.create_table(
        'terminology_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('preferred_term', sa.String(length=255), nullable=False),
        sa.Column('prohibited_term', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('match_type', sa.String(length=50), nullable=False, server_default='EXACT'),
        sa.Column('case_sensitive', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='BRAND_IDENTITY'),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='HIGH'),
        sa.Column('applicable_channel', sa.String(length=100), nullable=False, server_default='ALL'),
        sa.Column('applicable_region', sa.String(length=100), nullable=False, server_default='GLOBAL'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('source_document_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_document_id'], ['brand_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_rules_organisation_id'), 'terminology_rules', ['organisation_id'], unique=False)
    op.create_index(op.f('ix_terminology_rules_prohibited_term'), 'terminology_rules', ['prohibited_term'], unique=False)
    op.create_index(op.f('ix_terminology_rules_status'), 'terminology_rules', ['status'], unique=False)

    # 7. knowledge_approvals
    op.create_table(
        'knowledge_approvals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reviewer_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_approvals_organisation_id'), 'knowledge_approvals', ['organisation_id'], unique=False)
    op.create_index(op.f('ix_knowledge_approvals_entity_type'), 'knowledge_approvals', ['entity_type'], unique=False)
    op.create_index(op.f('ix_knowledge_approvals_entity_id'), 'knowledge_approvals', ['entity_id'], unique=False)
    op.create_index(op.f('ix_knowledge_approvals_created_at'), 'knowledge_approvals', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('knowledge_approvals')
    op.drop_table('terminology_rules')
    op.drop_table('approved_facts')
    op.drop_table('document_chunks')
    op.drop_table('document_versions')
    op.drop_table('brand_documents')
    op.drop_table('brand_profiles')

