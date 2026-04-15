import sqlite3
import os
import dbf
from datetime import datetime

SQLITE_DB = r"D:\PyZar\app1.db"
DBF_FOLDER = r"C:\CTMS\dbf"

TARGET_TABLES = ["ctms1000", "ctms4000", "ctms4100", "ctms9000"]

PRIMARY_KEYS = {
    "ctms1000": "CASEID",
    "ctms4000": "PERSONID",
    "ctms4100": "PARTYID",
    "ctms9000": "CASEID"
}

# =========================
# SQLITE MAP
# =========================
def get_sqlite_map(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    rows = cur.fetchall()
    return {r[1].upper(): r[1] for r in rows}

# =========================
# DBF FIELD TYPES
# =========================
def get_field_types(dbf_table):
    types = {}
    for f in dbf_table.structure():
        parts = f.split()
        name = parts[0].upper()
        types[name] = parts[1][0]
    return types

# =========================
# SAFE DATETIME
# =========================
def parse_dt(val):
    if not val:
        return datetime.min
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("T", " "))
    except:
        return datetime.min

# =========================
# CONVERT VALUE
# =========================
def convert_value(value, field_type):
    if value is None or value == "":
        return None

    try:
        if isinstance(value, str):
            value = value.strip()

        if field_type == 'N':
            try:
                return int(value) if str(value).isdigit() else float(value)
            except:
                return None

        if field_type == 'D':
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()

        if field_type == 'T':
            return parse_dt(value)

        return value

    except:
        return value

# =========================
# DBF INDEX
# =========================
def build_index(dbf_table, key):
    index = {}
    for r in dbf_table:
        try:
            index[str(getattr(r, key))] = r
        except:
            pass
    return index

# =========================
# SAFE GET (IMPORTANT FIX)
# =========================
def safe_get(rec, field):
    try:
        return getattr(rec, field)
    except:
        return None

# =========================
# SYNC ENGINE
# =========================
def sync_table(conn, table_name):
    dbf_path = os.path.join(DBF_FOLDER, f"{table_name.upper()}.DBF")

    if not os.path.exists(dbf_path):
        print(f"⏭ Missing DBF: {table_name}")
        return

    print(f"\n📦 Syncing {table_name}")

    key = PRIMARY_KEYS[table_name]

    dbf_table = dbf.Table(dbf_path)
    dbf_table.open(dbf.READ_WRITE)

    sqlite_map = get_sqlite_map(conn, table_name)
    dbf_cols = [c.upper() for c in dbf_table.field_names]
    dbf_types = get_field_types(dbf_table)

    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()

    index = build_index(dbf_table, key)

    inserted = updated = unchanged = skipped = 0

    for row in rows:
        sqlite_row = dict(zip(sqlite_map.keys(), row))
        pk = str(sqlite_row.get(key.upper()))

        try:
            found = index.get(pk)

            # =========================
            # BUILD FULL DBF ROW
            # =========================
            full_row = {}

            for col in dbf_cols:
                sql_col = sqlite_map.get(col)
                value = sqlite_row.get(sql_col) if sql_col else None
                full_row[col] = convert_value(value, dbf_types.get(col, 'C'))

            # =========================
            # UPDATE LOGIC (FIXED MODIFYDT)
            # =========================
            if found:
                sql_dt = sqlite_row.get("MODIFYDT")
                dbf_dt = safe_get(found, "MODIFYDT")

                dbf_has_modifydt = "MODIFYDT" in dbf_cols

                if dbf_has_modifydt:
                    should_update = parse_dt(sql_dt) > parse_dt(dbf_dt)
                else:
                    should_update = True  # IMPORTANT FIX

                if should_update:
                    print(f"🔄 Updating ID: {pk}")
                    with found:
                        for k, v in full_row.items():
                            setattr(found, k, v)
                    updated += 1
                else:
                    unchanged += 1

            # =========================
            # INSERT
            # =========================
            else:
                print(f"➕ Inserting ID: {pk}")
                dbf_table.append(full_row)
                inserted += 1

        except Exception as e:
            print(f"❌ ROW ERROR {pk}: {e}")
            skipped += 1

    dbf_table.close()

    print(f"\n✅ {table_name} → inserted {inserted}, updated {updated}, unchanged {unchanged}, skipped {skipped}")

# =========================
# MAIN
# =========================
def main():
    conn = sqlite3.connect(SQLITE_DB)

    print("\n🚀 CORE SYNC (FINAL STABLE VERSION)\n")

    for t in TARGET_TABLES:
        sync_table(conn, t)

    conn.close()

    print("\n🎉 SYNC COMPLETE")

if __name__ == "__main__":
    main()