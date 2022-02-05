from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table
from alembic import autogenerate
from alembic.operations import ops
import sqlalchemy


e = create_engine("sqlite:///annotations.db")

with e.connect() as conn:
    m = MetaData(e)
    m.reflect()
    
print(autogenerate.render_python_code(
    ops.UpgradeOps(
        ops=[
            ops.CreateTableOp.from_table(table) for table in m.tables.values()
        ] + [
            ops.CreateIndexOp.from_index(idx) for table in m.tables.values()
            for idx in table.indexes
        ]
    ))
)