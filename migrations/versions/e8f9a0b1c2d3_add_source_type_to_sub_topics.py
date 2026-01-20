"""add_source_type_to_sub_topics

Revision ID: e8f9a0b1c2d3
Revises: d4e5f6a7b8c9
Create Date: 2026-01-20 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """sub_topics 테이블에 source_type 컬럼 추가"""
    op.add_column('sub_topics', sa.Column('source_type', sa.String(), nullable=True, comment='핵심 정보 소스 타입 (text | youtube_url)'))


def downgrade() -> None:
    """sub_topics 테이블에서 source_type 컬럼 제거"""
    op.drop_column('sub_topics', 'source_type')
