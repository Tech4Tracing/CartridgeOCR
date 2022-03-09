"""add user table

Revision ID: 1a936d4b30b1
Revises: 5022eca857f6
Create Date: 2022-02-04 23:34:26.526223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a936d4b30b1'
down_revision = '5022eca857f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.String(128)),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('profile_pic', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table("user")
