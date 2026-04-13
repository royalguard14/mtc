from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import os

# =========================
# PATHS
# =========================
source_db = r"sqlite:///C:/Users/Supreme Court/Desktop/New folder/ctms2300.db"
target_db = r"sqlite:///C:/Users/Supreme Court/AppData/Local/PyZar-MTCBADN/app.db"

# =========================
# CONNECT TO BOTH DATABASES
# =========================
source_engine = create_engine(source_db)
target_engine = create_engine(target_db)

source_conn = source_engine.connect()
target_conn = target_engine.connect()

source_meta = MetaData()
target_meta = MetaData()

# =========================
# REFLECT TABLES
# =========================
source_table = Table("ctms2300", source_meta, autoload_with=source_engine)
target_table = Table("ctms2300", target_meta, autoload_with=target_engine)

# =========================
# READ ALL DATA FROM SOURCE
# =========================
rows = source_conn.execute(source_table.select()).fetchall()

print(f"📦 Found {len(rows)} rows in source DB")

# =========================
# INSERT INTO TARGET DB
# =========================
insert_count = 0

for row in rows:
    data = dict(row._mapping)

    # optional: avoid duplicates
    existing = target_conn.execute(
        target_table.select().where(
            target_table.c.CODEID == data["CODEID"]
        )
    ).fetchone()

    if not existing:
        target_conn.execute(target_table.insert().values(**data))
        insert_count += 1

target_conn.commit()

print(f"✅ Imported {insert_count} new records into app.db")