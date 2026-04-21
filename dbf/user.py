import os
import sqlite3
import argparse
from dbfread import DBF, FieldParser

# =========================
# ARGUMENTS
# =========================
parser = argparse.ArgumentParser(description="Convert DBF to SQLite")

parser.add_argument(
    "--filename",
    required=True,
    help="DBF filename only (e.g. ctms4100.dbf)"
)

parser.add_argument(
    "--output",
    default=r"C:\Users\Supreme Court\Desktop\New folder",
    help="Output folder for SQLite DB"
)

args = parser.parse_args()

# =========================
# STATIC BASE PATH
# =========================
base_path = r"C:\CTMS\dbf"

# Combine base path + filename
dbf_path = os.path.join(base_path, args.filename)

# Output folder
output_folder = args.output
os.makedirs(output_folder, exist_ok=True)

# Safety check
if not os.path.exists(dbf_path):
    raise FileNotFoundError(f"File not found in {base_path}: {args.filename}")

# Output SQLite (same name as DBF)
db_name = os.path.splitext(os.path.basename(dbf_path))[0] + ".db"
sqlite_path = os.path.join(output_folder, db_name)

table_name = os.path.splitext(os.path.basename(dbf_path))[0]

# =========================
# SAFE FIELD PARSER
# =========================
class SafeFieldParser(FieldParser):
    def parseN(self, field, data):
        try:
            return super().parseN(field, data)
        except:
            try:
                clean = data.strip().replace(b'\x00', b'')
                return float(clean)
            except:
                return None

# =========================
# TYPE MAPPING
# =========================
def dbf_type_to_sqlite(field):
    if field.type == 'N':
        return "REAL" if field.decimal_count > 0 else "INTEGER"
    elif field.type == 'F':
        return "REAL"
    elif field.type in ('C', 'M'):
        return "TEXT"
    elif field.type in ('D', 'T'):
        return "TEXT"
    elif field.type == 'L':
        return "INTEGER"
    elif field.type == 'I':
        return "INTEGER"
    else:
        return "TEXT"

# =========================
# CLEAN VALUES
# =========================
def clean_value(field, value):
    if value is None:
        return None

    if field.type == 'L':
        return 1 if value in (True, 'T', 't', 'Y', 'y', 1) else 0

    if field.type in ('D', 'T'):
        try:
            return value.isoformat()
        except:
            return str(value)

    if isinstance(value, str):
        value = value.strip().replace('\x00', '')
        try:
            return float(value) if '.' in value else int(value)
        except:
            return value

    return value

# =========================
# LOAD DBF
# =========================
print(f"Reading: {dbf_path}")

table = DBF(
    dbf_path,
    load=True,
    char_decode_errors='ignore',
    ignore_missing_memofile=True,
    parserclass=SafeFieldParser
)

fields = table.fields
field_names = [f.name for f in fields]

# =========================
# CREATE SQLITE
# =========================
print(f"Creating: {sqlite_path}")

conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

columns = []
for field in fields:
    col_type = dbf_type_to_sqlite(field)
    columns.append(f'"{field.name}" {col_type}')

create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)});'
cursor.execute(create_sql)

# =========================
# INSERT DATA
# =========================
placeholders = ", ".join(["?"] * len(field_names))
insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders});'

row_count = 0

for record in table:
    try:
        values = [
            clean_value(field, record.get(field.name))
            for field in fields
        ]

        cursor.execute(insert_sql, values)
        row_count += 1

    except Exception as e:
        print(f"⚠️ Skipped row: {e}")

# =========================
# SAVE
# =========================
conn.commit()
conn.close()

print(f"\n✅ DONE!")
print(f"Rows inserted: {row_count}")
print(f"SQLite saved at:\n{sqlite_path}")