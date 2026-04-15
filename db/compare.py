import sqlite3

old_db = r"C:\Users\Supreme Court\Desktop\New folder\combined1.db"
new_db = r"C:\Users\Supreme Court\Desktop\New folder\combined2.db"

def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def get_columns(conn, table):
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cursor.fetchall()]

def get_primary_key(conn, table):
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table}")')
    for row in cursor.fetchall():
        if row[5] == 1:  # pk column
            return row[1]
    return None

def fetch_table_data(conn, table, pk):
    cursor = conn.cursor()

    if pk:
        cursor.execute(f'SELECT * FROM "{table}"')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        data = {}
        for row in rows:
            record = dict(zip(columns, row))
            data[record[pk]] = record
        return data
    else:
        # fallback: use rowid
        cursor.execute(f'SELECT rowid, * FROM "{table}"')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        data = {}
        for row in rows:
            record = dict(zip(columns, row))
            data[record["rowid"]] = record
        return data

def compare_dbs(old_db, new_db):
    conn_old = sqlite3.connect(old_db)
    conn_new = sqlite3.connect(new_db)

    tables_old = set(get_tables(conn_old))
    tables_new = set(get_tables(conn_new))

    common_tables = tables_old.intersection(tables_new)

    print("\n🔍 Comparing databases...\n")

    for table in common_tables:
        print(f"\n📂 Table: {table}")

        pk = get_primary_key(conn_old, table)
        if pk:
            print(f"   🔑 Primary Key: {pk}")
        else:
            print("   ⚠️ No primary key, using rowid")

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

            # Compare columns
            for col in old_row.keys():
                if col == "rowid":
                    continue

                old_val = old_row.get(col)
                new_val = new_row.get(col)

                if old_val != new_val:
                    print(f"   ✏️ Row {key} | Column '{col}':")
                    print(f"      OLD → {old_val}")
                    print(f"      NEW → {new_val}")

    conn_old.close()
    conn_new.close()

# RUN
compare_dbs(old_db, new_db)