"""add ammo reference collections

Revision ID: fe0dac53ceab
Revises: 93a05f106c41
Create Date: 2023-07-02 10:12:56.930727

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe0dac53ceab'
down_revision = '93a05f106c41'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ammunition") as batch_op:
        batch_op.add_column(sa.Column('reference_collection', sa.String(length=36), nullable=True))


def downgrade():
    with op.batch_alter_table("ammunition") as batch_op:
        batch_op.drop_column('reference_collection')
