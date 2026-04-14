import sqlite3
import os
import dbf
from datetime import datetime

SQLITE_DB = r"D:\PyZar\app1.db"
DBF_FOLDER = r"C:\CTMS\dbf"

TARGET_TABLES = [
    "ctms1000",
    "ctms4000",
    "ctms4100",
    "ctms9000"
]

PRIMARY_KEYS = {
    "ctms1000": "CASEID",
    "ctms4000": "PERSONID",
    "ctms4100": "PARTYID",
    "ctms9000": "CASEID"
}


def get_columns_sqlite(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cur.fetchall()]


def get_field_types(dbf_table):
    field_types = {}
    for field_def in dbf_table.structure():
        parts = field_def.split()
        name = parts[0]
        type_char = parts[1][0]
        field_types[name] = type_char
    return field_types


def convert_value(value, field_type):
    if value is None or value == "":
        return None

    try:
        if isinstance(value, str):
            value = value.strip()

        # INTEGER
        if field_type == 'N' and str(value).isdigit():
            return int(value)

        # FLOAT
        if field_type == 'N' and '.' in str(value):
            return float(value)

        # DATE
        if field_type == 'D':
            return datetime.strptime(value[:10], "%Y-%m-%d").date()

        # DATETIME
        if field_type == 'T':
            try:
                return datetime.fromisoformat(value)
            except:
                return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")

        return value

    except:
        return value


def sync_table(conn, table_name):
    dbf_path = os.path.join(DBF_FOLDER, f"{table_name.upper()}.DBF")

    if not os.path.exists(dbf_path):
        print(f"⏭ DBF not found: {table_name}")
        return

    print(f"\n📦 Syncing {table_name}")

    key = PRIMARY_KEYS.get(table_name)
    if not key:
        print(f"⚠️ No PK for {table_name}")
        return

    try:
        dbf_table = dbf.Table(dbf_path)
        dbf_table.open(dbf.READ_WRITE)

        sql_cols = get_columns_sqlite(conn, table_name)
        dbf_cols = dbf_table.field_names
        field_types = get_field_types(dbf_table)

        common_cols = [c for c in sql_cols if c.upper() in dbf_cols]

        if key not in common_cols:
            print(f"❌ Key mismatch")
            dbf_table.close()
            return

        cur = conn.cursor()
        cur.execute(f'SELECT {",".join(common_cols)} FROM {table_name}')
        rows = cur.fetchall()

        inserted = 0
        updated = 0
        unchanged = 0
        skipped = 0

        for row in rows:
            data = dict(zip(common_cols, row))

            try:
                found = None

                for rec in dbf_table:
                    if str(getattr(rec, key)) == str(data[key]):
                        found = rec
                        break

                if found:
                    dbf_modify = str(getattr(found, "MODIFYDT", "") or "")
                    sql_modify = str(data.get("MODIFYDT", "") or "")

                    if sql_modify > dbf_modify:
                        with found:  # 🔥 THIS IS THE FIX
                            for col in common_cols:
                                try:
                                    val = convert_value(data[col], field_types.get(col.upper(), 'C'))
                                    setattr(found, col, val)
                                except:
                                    pass
                        updated += 1
                    else:
                        unchanged += 1

                else:
                    new_data = {}
                    for col in common_cols:
                        val = convert_value(data[col], field_types.get(col.upper(), 'C'))
                        new_data[col] = val

                    dbf_table.append(new_data)
                    inserted += 1

            except Exception as e:
                skipped += 1
                continue

        dbf_table.close()

        print(f"✅ {table_name} → inserted {inserted}, updated {updated}, unchanged {unchanged}, skipped {skipped}")

    except Exception as e:
        print(f"❌ ERROR {table_name}: {e}")


def main():
    conn = sqlite3.connect(SQLITE_DB)

    print("\n🚀 CORE SYNC (FIXED ENGINE)\n")

    for table in TARGET_TABLES:
        sync_table(conn, table)

    conn.close()

    print("\n🎉 SYNC COMPLETE")


if __name__ == "__main__":
    main()