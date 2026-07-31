"""change user id to bigint

Revision ID: ccda498a5ec4
Revises: 66d5ddbadb1d
Create Date: 2026-07-24 20:28:54.835154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccda498a5ec4'
down_revision: Union[str, Sequence[str], None] = '66d5ddbadb1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
  # Alter users.id
  op.alter_column('users', 'id',
    existing_type=sa.Integer(),
    type_=sa.BigInteger(),
    existing_nullable=False,
    autoincrement=False)   # since it's not autoincrement

  # Alter categories.owner_id (foreign key to users.id)
  op.alter_column('categories', 'owner_id',
    existing_type=sa.Integer(),
    type_=sa.BigInteger(),
    existing_nullable=True
    )

def downgrade():
  op.alter_column('categories', 'owner_id',
    existing_type=sa.BigInteger(),
    type_=sa.Integer(),
    existing_nullable=True)
  op.alter_column('users', 'id',
    existing_type=sa.BigInteger(),
    type_=sa.Integer(),
    existing_nullable=False,
    autoincrement=False)
