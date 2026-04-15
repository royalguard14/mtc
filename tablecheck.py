import sqlite3
import os
import dbf

SQLITE_DB = r"D:\PyZar\app1.db"
DBF_FOLDER = r"C:\CTMS\dbf"

TABLES = [
    "ctms1000",
    "ctms4000",
    "ctms4100",
    "ctms9000"
]


def get_sqlite_cols(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cur.fetchall()]


def get_dbf_cols(dbf_table):
    return dbf_table.field_names


def analyze_table(conn, table):
    dbf_path = os.path.join(DBF_FOLDER, f"{table.upper()}.DBF")

    print("\n" + "=" * 80)
    print(f"📦 ANALYZING: {table}")
    print("=" * 80)

    sqlite_cols = get_sqlite_cols(conn, table)

    if not os.path.exists(dbf_path):
        print("❌ DBF missing")
        return

    dbf_table = dbf.Table(dbf_path)
    dbf_table.open(dbf.READ_ONLY)

    dbf_cols = get_dbf_cols(dbf_table)

    sqlite_set = set(sqlite_cols)
    dbf_set = set(dbf_cols)

    # normalize case
    sqlite_upper = {c.upper(): c for c in sqlite_cols}
    dbf_upper = {c.upper(): c for c in dbf_cols}

    common = []
    sqlite_only = []
    dbf_only = []
    case_mismatch = []

    for c in sqlite_cols:
        if c.upper() in dbf_upper:
            dbf_name = dbf_upper[c.upper()]
            if c != dbf_name:
                case_mismatch.append((c, dbf_name))
            common.append(c)
        else:
            sqlite_only.append(c)

    for c in dbf_cols:
        if c.upper() not in sqlite_upper:
            dbf_only.append(c)

    print("\n🟢 COMMON (SAFE SYNC):")
    print(common)

    print("\n🟡 SQLITE ONLY (WILL NOT SYNC TO DBF):")
    print(sqlite_only)

    print("\n🔵 DBF ONLY (WILL NOT SYNC TO SQLITE):")
    print(dbf_only)

    print("\n⚠️ CASE MISMATCHES:")
    for a, b in case_mismatch:
        print(f"SQLite: {a}  ↔  DBF: {b}")

    dbf_table.close()

    return {
        "common": common,
        "sqlite_only": sqlite_only,
        "dbf_only": dbf_only,
        "case_mismatch": case_mismatch
    }


def main():
    conn = sqlite3.connect(SQLITE_DB)

    results = {}

    for t in TABLES:
        results[t] = analyze_table(conn, t)

    conn.close()

    print("\n🎉 SCHEMA ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()