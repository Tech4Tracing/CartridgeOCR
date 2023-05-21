"""separate image notes

Revision ID: 594f79cac933
Revises: 61f6b345ea73
Create Date: 2023-05-18 03:53:04.984689

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
import json
import uuid

# revision identifiers, used by Alembic.
revision = '594f79cac933'
down_revision = '61f6b345ea73'
branch_labels = None
depends_on = None

def generate_uuid():
    return str(uuid.uuid4())

def normalize_notes():
    connection = op.get_bind()
    results = connection.execute(sa.text("SELECT id, extra_data FROM images")).all()
    print(f"Number of rows = {len(results)}.")
    for image_id, extra_data in results:
        if extra_data:
            extra_data = json.loads(extra_data)
            if type(extra_data) is dict:
                print(f"normalizing extra_data {extra_data}")
                notes = []
                for k in extra_data:
                    notes.append({
                        "predictionId": None,
                        "key": k,
                        "value": extra_data[k]
                    })
                extra_data = json.dumps(notes)
                connection.execute(sa.text("UPDATE images SET extra_data = :extra_data WHERE id = :image_id"), 
                                   {'extra_data': extra_data, 'image_id': image_id})            

def upgrade():
    
    op.create_table(
        'notes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('image_id',  sa.String(length=36), nullable=False),
        sa.Column('prediction_id', sa.String(length=36), nullable=True),
        sa.Column('note_key', sa.String(255)),
        sa.Column('note_value', sa.Text),
        sa.PrimaryKeyConstraint('id')
    )
    
    with op.batch_alter_table("notes") as batch_op:
        batch_op.create_foreign_key('fk_notes_images', 'images', ['image_id'], ['id'])
    
    normalize_notes()

    # Move data from Images to Notes
    connection = op.get_bind()
    results = connection.execute(sa.text("SELECT id, extra_data FROM images")).all()
    print(f"Number of rows = {len(results)}.")
    for image_id, extra_data in results:
        if extra_data:
            extra_data = json.loads(extra_data)
            print(f'Migrating extra_data {extra_data})')
            for note in extra_data:
                try:
                    connection.execute(
                        sa.text("INSERT INTO notes (id, image_id, prediction_id, note_key, note_value) VALUES (:id, :image_id, :prediction_id, :note_key, :note_value)"),
                        {
                            'id': generate_uuid(),
                            'image_id': image_id,
                            'prediction_id': note["predictionId"],
                            'note_key': note["key"],
                            'note_value': note["value"]
                        }
                    )
                except Exception as e:
                    print(note)
                    raise e
    op.drop_column('images', 'extra_data')


def downgrade():
    # this will likely be a one-way upgrade due to the foreign key constraint
    pass