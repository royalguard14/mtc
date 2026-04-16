import sqlite3
import argparse
import os

# ==============================
# CONFIG: Base folder
# ==============================
BASE_DIR = r"D:\PyZar\forCompare"

# ==============================
# Argument parser
# ==============================
parser = argparse.ArgumentParser(description="Compare two SQLite databases")
parser.add_argument("--o", required=True, help="Old/source database file")
parser.add_argument("--n", required=True, help="New/target database file")
args = parser.parse_args()

# Resolve full paths
old_db = args.o if os.path.isabs(args.o) else os.path.join(BASE_DIR, args.o)
new_db = args.n if os.path.isabs(args.n) else os.path.join(BASE_DIR, args.n)

# Check if files exist
if not os.path.exists(old_db):
    print(f"❌ Old DB not found: {old_db}")
    exit()

if not os.path.exists(new_db):
    print(f"❌ New DB not found: {new_db}")
    exit()

print(f"📁 Old DB: {old_db}")
print(f"📁 New DB: {new_db}")

# ==============================
# Helper functions
# ==============================
def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def get_primary_key(conn, table):
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table}")')
    for row in cursor.fetchall():
        if row[5] == 1:
            return row[1]
    return None

def fetch_table_data(conn, table, pk):
    cursor = conn.cursor()

    if pk:
        cursor.execute(f'SELECT * FROM "{table}"')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return {
            dict(zip(columns, row))[pk]: dict(zip(columns, row))
            for row in rows
        }
    else:
        cursor.execute(f'SELECT rowid, * FROM "{table}"')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return {
            dict(zip(columns, row))["rowid"]: dict(zip(columns, row))
            for row in rows
        }

# ==============================
# Compare function
# ==============================
def compare_dbs(old_db, new_db):
    conn_old = sqlite3.connect(old_db)
    conn_new = sqlite3.connect(new_db)

    tables_old = set(get_tables(conn_old))
    tables_new = set(get_tables(conn_new))

    print("\n📊 Tables in OLD:", tables_old)
    print("📊 Tables in NEW:", tables_new)

    common_tables = tables_old.intersection(tables_new)

    if not common_tables:
        print("\n⚠️ No common tables found!")
        return

    print("\n🔍 Comparing databases...\n")

    changes_found = False

    for table in common_tables:
        print(f"\n📂 Table: {table}")

        pk = get_primary_key(conn_old, table)
        print(f"   🔑 Primary Key: {pk if pk else 'rowid (fallback)'}")

        old_data = fetch_table_data(conn_old, table, pk)
        new_data = fetch_table_data(conn_new, table, pk)

        all_keys = set(old_data.keys()).union(new_data.keys())

        for key in all_keys:
            old_row = old_data.get(key)
            new_row = new_data.get(key)

            if old_row and not new_row:
                print(f"   ❌ Deleted row: {key}")
                changes_found = True
                continue

            if not old_row and new_row:
                print(f"   ➕ New row: {key}")
                changes_found = True
                continue

            for col in old_row.keys():
                if col == "rowid":
                    continue

                if old_row[col] != new_row[col]:
                    print(f"   ✏️ Row {key} | Column '{col}':")
                    print(f"      OLD → {old_row[col]}")
                    print(f"      NEW → {new_row[col]}")
                    changes_found = True

    if not changes_found:
        print("\n✅ No differences found.")

    conn_old.close()
    conn_new.close()

# ==============================
# RUN
# ==============================
compare_dbs(old_db, new_db)