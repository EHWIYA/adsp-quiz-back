"""Add users table + wrong_answers.user_id (nullable for back-compat)."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "g1h2i3j4k5l6_users"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column(
        "wrong_answers",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_wrong_answers_user_id", "wrong_answers", ["user_id"])
    # per-user uniqueness: drop global unique on quiz_id if present, add composite
    try:
        op.drop_constraint("wrong_answers_quiz_id_key", "wrong_answers", type_="unique")
    except Exception:
        pass
    try:
        op.create_unique_constraint(
            "uq_wrong_answers_user_quiz", "wrong_answers", ["user_id", "quiz_id"]
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint("uq_wrong_answers_user_quiz", "wrong_answers", type_="unique")
    except Exception:
        pass
    op.drop_index("ix_wrong_answers_user_id", table_name="wrong_answers")
    op.drop_column("wrong_answers", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
