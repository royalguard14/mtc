import os
import sqlite3
from dbfread import DBF

# Folder containing DBF files
folder = r"C:\CTMS\dbf"
output_folder = r"C:\Users\Supreme Court\Desktop\New folder"

os.makedirs(output_folder, exist_ok=True)

# SQLite file will be created in the same folder
sqlite_path = os.path.join(output_folder, "combined1.db")

conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

def dbf_type_to_sqlite(field):
    """Map DBF field types to SQLite types"""
    if field.type == 'N':  # Numeric
        return "REAL" if field.decimal_count > 0 else "INTEGER"
    elif field.type == 'F':  # Float
        return "REAL"
    elif field.type == 'C':  # Character
        return "TEXT"
    elif field.type == 'M':  # Memo
        return "TEXT"
    elif field.type == 'D':  # Date
        return "TEXT"  # stored as YYYY-MM-DD
    elif field.type == 'L':  # Logical
        return "INTEGER"  # 0/1
    elif field.type == 'I':  # Integer
        return "INTEGER"
    elif field.type == 'T':  # Datetime
        return "TEXT"
    else:
        return "TEXT"

for filename in os.listdir(folder):
    if filename.lower().endswith(".dbf"):
        dbf_path = os.path.join(folder, filename)

        table_name = os.path.splitext(filename)[0]

        print(f"Processing {filename} → table `{table_name}`")

        table = DBF(dbf_path, load=True)

        fields = table.fields  # full field objects (not just names)

        # Build CREATE TABLE with proper types
        columns = []
        for field in fields:
            sql_type = dbf_type_to_sqlite(field)
            columns.append(f'"{field.name}" {sql_type}')

        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)});'
        cursor.execute(create_sql)

        # Insert data
        field_names = [f.name for f in fields]
        placeholders = ", ".join(["?"] * len(field_names))

        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders});'

        for record in table:
            values = []
            for field in fields:
                value = record.get(field.name)

                # Convert DBF types properly
                if field.type == 'L':  # Logical → 0/1
                    value = 1 if value in (True, 'T', 't', 'Y', 'y') else 0 if value in (False, 'F', 'f', 'N', 'n') else None
                elif field.type == 'D':  # Date → string YYYY-MM-DD
                    value = value.isoformat() if value else None
                elif field.type == 'T':  # Datetime → string
                    value = value.isoformat() if value else None

                values.append(value)

            cursor.execute(insert_sql, values)

conn.commit()
conn.close()

print(f"✅ Done! SQLite saved at: {sqlite_path}")
