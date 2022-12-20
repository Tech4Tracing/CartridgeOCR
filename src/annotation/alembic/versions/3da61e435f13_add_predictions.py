"""add predictions

Revision ID: 3da61e435f13
Revises: ccabf4d80f27
Create Date: 2022-12-20 10:26:18.811709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3da61e435f13'
down_revision = 'ccabf4d80f27'
branch_labels = None
depends_on = None


def upgrade():
    if False:  # this code is handled by models/base.py
        op.create_table('predictions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('image_id', sa.String(length=36), nullable=True),
        sa.Column('casing_box', sa.Text(), nullable=True),
        sa.Column('casing_confidence', sa.Float(), nullable=True),
        sa.Column('primer_box', sa.Text(), nullable=True),
        sa.Column('primer_confidence', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'))

    with op.batch_alter_table("predictions") as batch_op:
        batch_op.create_foreign_key('fk_predictions_images', 'images', ['image_id'], ['id'])
    
    ## update the images table

    with op.batch_alter_table("images") as batch_op:
        batch_op.add_column(sa.Column('prediction_status', sa.Text(), nullable=True))
    with op.batch_alter_table("annotations") as batch_op:
        batch_op.add_column(sa.Column('prediction_id', sa.String(length=36), nullable=True))


def downgrade():
    with op.batch_alter_table("images") as batch_op:
        batch_op.drop_column('prediction_status')
    with op.batch_alter_table("annotations") as batch_op:
        batch_op.drop_column('prediction_id')
    op.drop_constraint(None, 'predictions', type_='foreignkey') ## likely to fail
    op.drop_table('predictions')

