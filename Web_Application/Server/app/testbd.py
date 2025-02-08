from sqlalchemy import inspect
from models import engine  # Assure-toi que c'est le bon engine

inspector = inspect(engine)
for table in inspector.get_table_names():
    print(f"Table: {table}")
    for column in inspector.get_columns(table):
        print(f"  - {column['name']} ({column['type']})")

