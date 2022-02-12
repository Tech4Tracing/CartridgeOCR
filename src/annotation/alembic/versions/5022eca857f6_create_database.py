"""create database

Revision ID: 5022eca857f6
Revises: 
Create Date: 2022-02-03 22:18:02.090328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5022eca857f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('alembic_version',
        sa.Column('version_num', sa.VARCHAR(length=32), nullable=False),
        sa.PrimaryKeyConstraint('version_num', name='alembic_version_pkc')
    )
    op.create_table('annotations',
        sa.Column('anno_id', sa.INTEGER(), nullable=True),
        sa.Column('img_id', sa.INTEGER(), nullable=True),
        sa.Column('geometry', sa.TEXT(), nullable=True),
        sa.Column('annotation', sa.TEXT(), nullable=True),
        sa.Column('metadata', sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint('anno_id')
    )
    op.create_table('globals',
        sa.Column('key', sa.TEXT(), nullable=True),
        sa.Column('value', sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )
    op.create_table('images',
        sa.Column('img_id', sa.INTEGER(), nullable=True),
        sa.Column('filename', sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint('img_id')
    )

def downgrade():
    pass
