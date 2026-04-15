import sqlite3

old_db = r"C:\Users\Supreme Court\Desktop\New folder\combined1.db"
new_db = r"C:\Users\Supreme Court\Desktop\New folder\combined2.db"


def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]


def get_primary_key(conn, table):
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table}")')

    for row in cursor.fetchall():
        if row[5] == 1:  # pk flag
            return row[1]
    return None


def fetch_table_data(conn, table, pk):
    cursor = conn.cursor()

    cursor.execute(f'SELECT * FROM "{table}"')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    data = {}

    for row in rows:
        record = dict(zip(columns, row))

        # skip if key missing (extra safety)
        if pk not in record:
            continue

        data[record[pk]] = record

    return data

def compare_dbs(old_db, new_db):
    conn_old = sqlite3.connect(old_db)
    conn_new = sqlite3.connect(new_db)

    tables_old = get_tables(conn_old)
    tables_new = get_tables(conn_new)

    common_tables = set(tables_old).intersection(set(tables_new))

    print("\n🔍 Comparing databases...\n")
    print("COMMON TABLES:", common_tables)

    for table in common_tables:

        pk = get_primary_key(conn_old, table)

        print(f"\n📂 Table: {table}")
        print(f"   🔑 Primary Key: {pk}")

        if not pk:
            print("   ⚠️ SKIPPED (no primary key)")
            continue

        old_data = fetch_table_data(conn_old, table, pk)
        new_data = fetch_table_data(conn_new, table, pk)

        all_keys = set(old_data.keys()).union(new_data.keys())

        for key in all_keys:
            old_row = old_data.get(key)
            new_row = new_data.get(key)

            if old_row and not new_row:
                print(f"   ❌ Deleted row: {key}")
                continue

            if not old_row and new_row:
                print(f"   ➕ New row: {key}")
                continue

            for col in old_row.keys():
                if col == pk:
                    continue

                if old_row.get(col) != new_row.get(col):
                    print(f"   ✏️ Row {key} | Column '{col}':")
                    print(f"      OLD → {old_row.get(col)}")
                    print(f"      NEW → {new_row.get(col)}")

    conn_old.close()
    conn_new.close()


# RUN
compare_dbs(old_db, new_db)