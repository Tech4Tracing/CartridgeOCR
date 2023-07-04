"""add public user

Revision ID: 93a05f106c41
Revises: 4d06fc454a63
Create Date: 2023-07-02 08:05:26.916052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93a05f106c41'
down_revision = '4d06fc454a63'
branch_labels = None
depends_on = None

PUBLIC_SCOPE_USER_EMAIL = "public@tech4tracing.org"
PUBLIC_SCOPE_USER_ID = "00000000-0000-0000-0000-000000000000" 

def upgrade():
    connection = op.get_bind()

    connection.execute(
        sa.text("INSERT INTO users (id, provider_id, name, email, profile_pic, is_active, is_superuser) VALUES (:id, :provider_id, :name, :email, :profile_pic, :is_active, :is_superuser)"),
        {
            'id': PUBLIC_SCOPE_USER_ID,
            'provider_id': "tech4tracing00000000",
            'name': "Public User",
            'email': PUBLIC_SCOPE_USER_EMAIL,
            'profile_pic': "",
            'is_active': False,
            'is_superuser': False
        }        
    )


def downgrade():
    connection = op.get_bind()

    connection.execute(
        sa.text("DELETE FROM users WHERE id = :id"),
        {
            'id': PUBLIC_SCOPE_USER_ID
        }
    )
