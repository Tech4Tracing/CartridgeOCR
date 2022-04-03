"""update annotations table

Revision ID: ca85af32845c
Revises: c6fcb18c2440
Create Date: 2022-04-03 07:36:55.865506

"""
from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers, used by Alembic.
revision = 'ca85af32845c'
down_revision = 'c6fcb18c2440'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('annotations', schema=None) as batch_op: 
        #batch_op.drop_column('anno_id')
        #batch_op.add_column(sa.Column('anno_id', sa.String(36), nullable=False))
        #batch_op.create_primary_key('annotations_pkey', ['anno_id'])
        #batch_op.drop_column('img_id')
        #batch_op.add_column(sa.Column('img_id', sa.String(36), nullable=False))
        
        # mssql requires dropping the primary key constraint first.
        if context.get_impl().bind.dialect.name == "mssql":
            print('Dropping PK constraint')
            #batch_op.execute("DECLARE @name AS VARCHAR; SELECT @name= MAX(NAME) FROM sys.key_constraints WHERE type = N'PK' AND parent_object_id = OBJECT_ID(N'dbo.annotations');")            
            batch_op.execute("""
DECLARE @sql    nvarchar(max) = N'',
        @table  nvarchar(513) = QUOTENAME(N'annotations'),
        @column nvarchar(128) = QUOTENAME(N'anno_id');

SELECT @sql += N'ALTER TABLE dbo.' 
    + @table + N' DROP CONSTRAINT ' 
    + QUOTENAME(name) + N';'
  FROM sys.key_constraints
  WHERE type = N'PK' AND parent_object_id = OBJECT_ID(N'dbo.' + @table);

EXEC sys.sp_executesql @sql;
            """)
        batch_op.drop_column('anno_id')
        batch_op.add_column(sa.Column('anno_id', sa.String(36), nullable=False))
        batch_op.create_primary_key('annotations_pkey', ['anno_id'])
        
        batch_op.alter_column('img_id', existing_type=sa.Integer(), type_=sa.String(36))
        batch_op.add_column(sa.Column('user_id', sa.String(length=255), nullable=True))
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('annotations', 'user_id')
    # TODO: this will likely fail on mssql
    with op.batch_alter_table('annotations', schema=None) as batch_op: 
        batch_op.alter_column('anno_id', type_=sa.Integer(), existing_type=sa.String(36))
        batch_op.alter_column('img_id', type_=sa.Integer(), existing_type=sa.String(36))
    # ### end Alembic commands ###
