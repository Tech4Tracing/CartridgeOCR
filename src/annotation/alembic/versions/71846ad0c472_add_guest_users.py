"""add guest users

Revision ID: 71846ad0c472
Revises: 3da61e435f13
Create Date: 2022-12-30 12:23:31.217529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71846ad0c472'
down_revision = '3da61e435f13'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("imagecollections") as batch_op:
        batch_op.add_column(sa.Column('guest_users', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("imagecollections") as batch_op:
        batch_op.drop_column('guest_users')
