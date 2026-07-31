"""making username column nullable

Revision ID: 66d5ddbadb1d
Revises: 666711563071
Create Date: 2026-07-23 07:15:25.335105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66d5ddbadb1d'
down_revision: Union[str, Sequence[str], None] = '666711563071'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "username", nullable = True)


def downgrade() -> None:
    op.alter_column("users", "username", nullable = False)
