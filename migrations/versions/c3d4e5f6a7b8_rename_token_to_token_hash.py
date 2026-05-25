"""rename revoked token column to token_hash

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-21 12:00:01.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('revoked_tokens') as batch_op:
        batch_op.alter_column(
            'token',
            new_column_name='token_hash',
            existing_type=sa.String(),
            type_=sa.String(length=64),
        )
        batch_op.create_unique_constraint(
            'uq_revoked_tokens_token_hash',
            ['token_hash'],
        )


def downgrade() -> None:
    with op.batch_alter_table('revoked_tokens') as batch_op:
        batch_op.drop_constraint(
            'uq_revoked_tokens_token_hash',
            type_='unique',
        )
        batch_op.alter_column(
            'token_hash',
            new_column_name='token',
            existing_type=sa.String(length=64),
            type_=sa.String(),
        )
