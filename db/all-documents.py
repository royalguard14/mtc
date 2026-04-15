import os
import sqlite3
from dbfread import DBF, FieldParser

# =========================
# CONFIG
# =========================
folder = r"C:\CTMS\documents"
output_folder = r"C:\CTMS\db"
sqlite_path = os.path.join(output_folder, "merge_dbf.db")

# =========================
# SAFE FIELD PARSER (FIX DBF ERROR)
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
# HELPER FUNCTIONS
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
# CONNECT SQLITE
# =========================
conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

table_created = False
field_names = []
field_names_no_caseid = []

# =========================
# PROCESS DBF FILES
# =========================
for filename in os.listdir(folder):
    if filename.lower().endswith(".dbf"):
        dbf_path = os.path.join(folder, filename)

        print(f"Processing {filename}")

        try:
            table = DBF(
                dbf_path,
                load=True,
                char_decode_errors='ignore',
                ignore_missing_memofile=True,
                parserclass=SafeFieldParser   # ⭐ IMPORTANT FIX
            )
        except Exception as e:
            print(f"❌ Failed to read {filename}: {e}")
            continue

        fields = table.fields

        # =========================
        # CREATE TABLE (FIRST FILE ONLY)
        # =========================
        if not table_created:
            field_names = [f.name for f in fields]

            field_names_no_caseid = [f for f in field_names if f.upper() != "CASEID"]

            columns = []
            for field in fields:
                col_type = dbf_type_to_sqlite(field)
                columns.append(f'"{field.name}" {col_type}')

            create_sql = f'CREATE TABLE IF NOT EXISTS combine ({", ".join(columns)});'
            cursor.execute(create_sql)

            table_created = True

            print("✅ Table 'combine' created")

        # =========================
        # PREPARE INSERT
        # =========================
        insert_sql = f'INSERT INTO combine VALUES ({", ".join(["?"] * len(field_names))});'

        # Get CASENUM index
        try:
            casenum_index = field_names.index("CASENUM")
        except ValueError:
            print("❌ CASENUM column not found!")
            exit()

        # =========================
        # INSERT ROWS
        # =========================
        for record in table:
            try:
                values = [
                    clean_value(field, record.get(field.name))
                    for field in fields
                ]

                casenum_value = values[casenum_index]

                # Check if CASENUM already exists
                cursor.execute(
                    'SELECT 1 FROM combine WHERE CASENUM = ? LIMIT 1;',
                    (casenum_value,)
                )

                if cursor.fetchone():
                    continue  # skip duplicate CASENUM

                cursor.execute(insert_sql, values)

            except Exception as e:
                print(f"⚠️ Skipped row: {e}")
                continue

# =========================
# SAVE
# =========================
conn.commit()
conn.close()

print(f"\n✅ DONE!\nSQLite saved at:\n{sqlite_path}")
