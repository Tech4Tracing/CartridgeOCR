"""Create ammunition table

Revision ID: 4d06fc454a63
Revises: 594f79cac933
Create Date: 2023-06-18 08:31:48.254146

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
import uuid

# revision identifiers, used by Alembic.
revision = '4d06fc454a63'
down_revision = '594f79cac933'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ammunition',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('caliber', sa.String(length=255), nullable=True),
    sa.Column('cartridge_type', sa.String(length=255), nullable=True),
    sa.Column('casing_material', sa.String(length=255), nullable=True),
    sa.Column('country', sa.String(length=255), nullable=True),
    sa.Column('manufacturer', sa.String(length=255), nullable=True),
    sa.Column('year_start', sa.Integer(), nullable=True),
    sa.Column('year_end', sa.Integer(), nullable=True),
    sa.Column('headstamp_markings', sa.String(length=255), nullable=True),
    sa.Column('projectile', sa.String(length=255), nullable=True),
    sa.Column('casing_description', sa.String(length=255), nullable=True),
    sa.Column('primer', sa.String(length=255), nullable=True),
    sa.Column('data_source', sa.String(length=255), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.Column('headstamp_image', sa.String(length=36), nullable=True),
    sa.Column('profile_image', sa.String(length=36), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    # TODO: does this table need a foreign key constraint for the associated images?
    

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ammunition')
    # ### end Alembic commands ###