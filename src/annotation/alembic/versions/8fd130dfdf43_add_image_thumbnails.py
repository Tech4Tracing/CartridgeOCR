"""add image thumbnails

Revision ID: 8fd130dfdf43
Revises: fe0dac53ceab
Create Date: 2023-11-18 09:40:20.963775

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fd130dfdf43'
down_revision = 'fe0dac53ceab'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("images") as batch_op:
        batch_op.add_column(sa.Column('thumbnailStorageKey', sa.String(length=1024), nullable=True))

def downgrade():
    with op.batch_alter_table("images") as batch_op:
        batch_op.drop_column('thumbnailStorageKey')
