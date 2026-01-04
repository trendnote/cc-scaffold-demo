"""add_performance_metadata_to_search_responses

Revision ID: ae10ee2e618d
Revises: f448da6ffc1c
Create Date: 2026-01-04 09:48:22.118405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ae10ee2e618d'
down_revision: Union[str, Sequence[str], None] = 'f448da6ffc1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add performance and metadata JSONB columns to search_responses
    op.add_column(
        'search_responses',
        sa.Column(
            'performance',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Performance metrics (embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms)'
        )
    )
    op.add_column(
        'search_responses',
        sa.Column(
            'response_metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Response metadata (is_fallback, fallback_reason, model_used, search_result_count)'
        )
    )

    # Make response_time_ms nullable (since we now have total_time_ms in performance)
    op.alter_column(
        'search_responses',
        'response_time_ms',
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Make response_time_ms non-nullable again
    op.alter_column(
        'search_responses',
        'response_time_ms',
        existing_type=sa.Integer(),
        nullable=False
    )

    # Remove performance and response_metadata columns
    op.drop_column('search_responses', 'response_metadata')
    op.drop_column('search_responses', 'performance')
