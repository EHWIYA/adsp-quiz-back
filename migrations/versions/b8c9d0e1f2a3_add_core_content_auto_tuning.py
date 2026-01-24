"""add_core_content_auto_tuning

Revision ID: b8c9d0e1f2a3
Revises: f1a2b3c4d5e6
Create Date: 2026-01-24 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """자동 분류 설정/로그/규칙 테이블 추가"""
    op.create_table(
        "core_content_auto_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("min_confidence", sa.Float, nullable=False),
        sa.Column("strategy", sa.String(length=30), nullable=False),
        sa.Column("keyword_weight", sa.Float, nullable=False),
        sa.Column("similarity_weight", sa.Float, nullable=False),
        sa.Column("max_candidates", sa.Integer, nullable=False),
        sa.Column("text_preview_length", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_table(
        "core_content_category_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sub_topic_id", sa.Integer, sa.ForeignKey("sub_topics.id"), nullable=False),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_core_content_category_rules_sub_topic_id", "core_content_category_rules", ["sub_topic_id"], unique=True)
    
    op.create_table(
        "core_content_auto_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("request_core_content", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("classification_text_preview", sa.Text, nullable=False),
        sa.Column("classification_text_hash", sa.String(length=64), nullable=False),
        sa.Column("auto_sub_topic_id", sa.Integer, sa.ForeignKey("sub_topics.id"), nullable=True),
        sa.Column("auto_confidence", sa.Float, nullable=True),
        sa.Column("final_sub_topic_id", sa.Integer, sa.ForeignKey("sub_topics.id"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("strategy", sa.String(length=30), nullable=False),
        sa.Column("min_confidence", sa.Float, nullable=False),
        sa.Column("keyword_weight", sa.Float, nullable=False),
        sa.Column("similarity_weight", sa.Float, nullable=False),
        sa.Column("max_candidates", sa.Integer, nullable=False),
        sa.Column("candidate_count", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_core_content_auto_runs_status", "core_content_auto_runs", ["status"])
    op.create_index("ix_core_content_auto_runs_auto_sub_topic_id", "core_content_auto_runs", ["auto_sub_topic_id"])
    op.create_index("ix_core_content_auto_runs_final_sub_topic_id", "core_content_auto_runs", ["final_sub_topic_id"])
    
    op.create_table(
        "core_content_auto_candidates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("core_content_auto_runs.id"), nullable=False),
        sa.Column("sub_topic_id", sa.Integer, sa.ForeignKey("sub_topics.id"), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("category_path", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_core_content_auto_candidates_run_id", "core_content_auto_candidates", ["run_id"])
    op.create_index("ix_core_content_auto_candidates_sub_topic_id", "core_content_auto_candidates", ["sub_topic_id"])
    
    op.create_table(
        "core_content_auto_overrides",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("core_content_auto_runs.id"), nullable=False),
        sa.Column("auto_sub_topic_id", sa.Integer, sa.ForeignKey("sub_topics.id"), nullable=True),
        sa.Column("final_sub_topic_id", sa.Integer, sa.ForeignKey("sub_topics.id"), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_core_content_auto_overrides_run_id", "core_content_auto_overrides", ["run_id"])
    
    settings_table = sa.table(
        "core_content_auto_settings",
        sa.column("id", sa.Integer),
        sa.column("min_confidence", sa.Float),
        sa.column("strategy", sa.String),
        sa.column("keyword_weight", sa.Float),
        sa.column("similarity_weight", sa.Float),
        sa.column("max_candidates", sa.Integer),
        sa.column("text_preview_length", sa.Integer),
    )
    op.bulk_insert(
        settings_table,
        [
            {
                "id": 1,
                "min_confidence": 0.3,
                "strategy": "hybrid",
                "keyword_weight": 0.5,
                "similarity_weight": 0.5,
                "max_candidates": 3,
                "text_preview_length": 200,
            }
        ],
    )


def downgrade() -> None:
    """자동 분류 설정/로그/규칙 테이블 삭제"""
    op.drop_index("ix_core_content_auto_overrides_run_id", table_name="core_content_auto_overrides")
    op.drop_table("core_content_auto_overrides")
    
    op.drop_index("ix_core_content_auto_candidates_sub_topic_id", table_name="core_content_auto_candidates")
    op.drop_index("ix_core_content_auto_candidates_run_id", table_name="core_content_auto_candidates")
    op.drop_table("core_content_auto_candidates")
    
    op.drop_index("ix_core_content_auto_runs_final_sub_topic_id", table_name="core_content_auto_runs")
    op.drop_index("ix_core_content_auto_runs_auto_sub_topic_id", table_name="core_content_auto_runs")
    op.drop_index("ix_core_content_auto_runs_status", table_name="core_content_auto_runs")
    op.drop_table("core_content_auto_runs")
    
    op.drop_index("ix_core_content_category_rules_sub_topic_id", table_name="core_content_category_rules")
    op.drop_table("core_content_category_rules")
    
    op.drop_table("core_content_auto_settings")
