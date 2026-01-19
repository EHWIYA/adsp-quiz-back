"""add_main_topic_and_sub_topic_models

Revision ID: a1b2c3d4e5f6
Revises: 2f68a60ba812
Create Date: 2026-01-17 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2f68a60ba812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # main_topics 테이블 생성
    op.create_table(
        'main_topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # sub_topics 테이블 생성
    op.create_table(
        'sub_topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('main_topic_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('core_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['main_topic_id'], ['main_topics.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # quizzes 테이블에 sub_topic_id 컬럼 추가
    op.add_column('quizzes', sa.Column('sub_topic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_quizzes_sub_topic_id', 'quizzes', 'sub_topics', ['sub_topic_id'], ['id'])
    op.create_index(op.f('ix_quizzes_sub_topic_id'), 'quizzes', ['sub_topic_id'], unique=False)


def downgrade() -> None:
    # quizzes 테이블에서 sub_topic_id 컬럼 제거
    op.drop_index(op.f('ix_quizzes_sub_topic_id'), table_name='quizzes')
    op.drop_constraint('fk_quizzes_sub_topic_id', 'quizzes', type_='foreignkey')
    op.drop_column('quizzes', 'sub_topic_id')
    
    # sub_topics 테이블 삭제
    op.drop_table('sub_topics')
    
    # main_topics 테이블 삭제
    op.drop_table('main_topics')
