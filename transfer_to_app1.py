import sqlite3

source_db = r"C:\Users\Supreme Court\Desktop\New folder\combined2.db"
target_db = r"D:\PyZar\app1.db"


def get_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return set(row[0] for row in cur.fetchall())


def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cur.fetchall()]


def copy_table(src_conn, dst_conn, table):
    try:
        src_cols = get_columns(src_conn, table)
        dst_cols = get_columns(dst_conn, table)

        common_cols = [c for c in src_cols if c in dst_cols]

        if not common_cols:
            print(f"⏭ SKIP {table} (no matching columns)")
            return

        col_list = ",".join([f'"{c}"' for c in common_cols])
        placeholders = ",".join(["?"] * len(common_cols))

        src_cur = src_conn.cursor()
        dst_cur = dst_conn.cursor()

        src_cur.execute(f'SELECT {col_list} FROM "{table}"')
        rows = src_cur.fetchall()

        if not rows:
            print(f"⚠️ {table} empty")
            return

        dst_cur.execute(f'DELETE FROM "{table}"')

        inserted = 0
        skipped = 0

        for row in rows:
            try:
                dst_cur.execute(
                    f'INSERT OR IGNORE INTO "{table}" ({col_list}) VALUES ({placeholders})',
                    row
                )
                inserted += 1

            except Exception as e:
                skipped += 1

                # 🔥 BUILD INSERT SQL FOR DEBUGGING
                values = []
                for v in row:
                    if v is None:
                        values.append("NULL")
                    elif isinstance(v, str):
                        values.append(f"'{v.replace('\'', '\'\'')}'")
                    else:
                        values.append(str(v))

                sql = f'INSERT INTO {table} ({col_list}) VALUES ({", ".join(values)});'

                print("\n❌ SKIPPED ROW")
                print("📌 ERROR:", e)
                print("🧾 FIX SQL:")
                print(sql)
                print("-" * 60)

                continue

        dst_conn.commit()

        print(f"\n✅ {table} → inserted {inserted}, skipped {skipped}\n")

    except Exception as e:
        print(f"❌ ERROR {table}: {e}")

def main():
    src = sqlite3.connect(source_db)
    dst = sqlite3.connect(target_db)

    src_tables = get_tables(src)
    dst_tables = get_tables(dst)

    print("\n🚀 SMART SYNC START\n")

    # ONLY tables that exist in BOTH DBs
    common_tables = src_tables & dst_tables

    for table in sorted(common_tables):
        print(f"📦 Processing {table}")
        copy_table(src, dst, table)

    # IMPORTANT: app-only tables are untouched
    extra_tables = dst_tables - src_tables
    if extra_tables:
        print("\n🟡 Skipped app-only tables:")
        for t in extra_tables:
            print(f"   - {t}")

    src.close()
    dst.close()

    print("\n🎉 SYNC COMPLETE (SAFE MODE)")


if __name__ == "__main__":
    main()