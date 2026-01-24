"""add_wrong_answers_table

Revision ID: f1a2b3c4d5e6
Revises: 97367266b36e
Create Date: 2026-01-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '97367266b36e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """wrong_answers 테이블 생성"""
    op.create_table(
        'wrong_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.Text(), nullable=False),
        sa.Column('selected_answer', sa.Integer(), nullable=False),
        sa.Column('correct_answer', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('sub_topic_id', sa.Integer(), nullable=True),
        sa.Column('created_at_original', sa.DateTime(timezone=True), nullable=True, comment='원본 문제의 created_at'),
        sa.Column('saved_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.ForeignKeyConstraint(['sub_topic_id'], ['sub_topics.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quiz_id'),
    )
    op.create_index(op.f('ix_wrong_answers_quiz_id'), 'wrong_answers', ['quiz_id'], unique=True)
    op.create_index(op.f('ix_wrong_answers_subject_id'), 'wrong_answers', ['subject_id'], unique=False)
    op.create_index(op.f('ix_wrong_answers_sub_topic_id'), 'wrong_answers', ['sub_topic_id'], unique=False)
    op.create_index(op.f('ix_wrong_answers_saved_at'), 'wrong_answers', ['saved_at'], unique=False)


def downgrade() -> None:
    """wrong_answers 테이블 제거"""
    op.drop_index(op.f('ix_wrong_answers_saved_at'), table_name='wrong_answers')
    op.drop_index(op.f('ix_wrong_answers_sub_topic_id'), table_name='wrong_answers')
    op.drop_index(op.f('ix_wrong_answers_subject_id'), table_name='wrong_answers')
    op.drop_index(op.f('ix_wrong_answers_quiz_id'), table_name='wrong_answers')
    op.drop_table('wrong_answers')
