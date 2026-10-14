
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import sys

# SOURCE: database na kukunan ng records
SOURCE_DB = Path(r"D:\PyZar\forCompare\zear.db")

# DESTINATION: database na lilinisin at lalagyan ng records
DEST_DB = Path(r"C:\CTMS\dbf\CTMS1000.db")

TABLE = "ctms1000"


def is_sqlite_database(path):
    """Tinitingnan kung SQLite database ang file."""
    if not path.exists() or not path.is_file():
        return False

    with open(path, "rb") as f:
        return f.read(16) == b"SQLite format 3\x00"


def quote_identifier(name):
    """Safe na paglalagay ng table/column names sa SQL."""
    return '"' + name.replace('"', '""') + '"'


def get_columns(conn, table):
    rows = conn.execute(
        f"PRAGMA table_info({quote_identifier(table)})"
    ).fetchall()

    if not rows:
        raise RuntimeError(f"Walang table na '{table}'.")

    return [row[1] for row in rows]


def main():
    print("=" * 55)
    print(" CTMS1000 DATABASE REPLACEMENT")
    print("=" * 55)

    # 1. Check files
    if not SOURCE_DB.exists():
        print(f"ERROR: Hindi makita ang source:\n{SOURCE_DB}")
        return

    if not DEST_DB.exists():
        print(f"ERROR: Hindi makita ang destination:\n{DEST_DB}")
        return

    # Important: CTMS may use DBF files, not SQLite.
    if not is_sqlite_database(SOURCE_DB):
        print("ERROR: Ang source file ay hindi SQLite database.")
        print("Hindi binago ang anumang file.")
        return

    if not is_sqlite_database(DEST_DB):
        print("ERROR: Ang destination file ay hindi SQLite database.")
        print("Maaaring DBF/Visual FoxPro table ito.")
        print("Hindi binago ang anumang file.")
        return

    source = None
    destination = None
    transaction_started = False

    try:
        source = sqlite3.connect(
            f"file:{SOURCE_DB.as_posix()}?mode=ro",
            uri=True
        )
        destination = sqlite3.connect(str(DEST_DB))

        # 2. Kunin ang columns at records
        source_columns = get_columns(source, TABLE)
        destination_columns = get_columns(destination, TABLE)

        if set(source_columns) != set(destination_columns):
            print("ERROR: Hindi magkapareho ang columns ng dalawang table.")
            print("\nSource columns:")
            print(source_columns)
            print("\nDestination columns:")
            print(destination_columns)
            print("\nWalang binagong records.")
            return

        columns = destination_columns
        quoted_columns = ", ".join(
            quote_identifier(column) for column in columns
        )

        source_rows = source.execute(
            f"SELECT {quoted_columns} FROM {quote_identifier(TABLE)}"
        )

        # I-check muna kung may laman ang source
        first_row = source_rows.fetchone()
        if first_row is None:
            print("ERROR: Walang records sa source ctms1000.")
            print("Hindi lilinisin ang destination.")
            return

        # 3. Backup ng destination database bago baguhin
        backup_path = DEST_DB.with_name(
            f"{DEST_DB.stem}_backup_"
            f"{datetime.now():%Y%m%d_%H%M%S}{DEST_DB.suffix}"
        )

        backup_conn = sqlite3.connect(str(backup_path))
        try:
            destination.backup(backup_conn)
        finally:
            backup_conn.close()

        print(f"\nBackup ginawa:\n{backup_path}")

        # 4. Kumpirmahin bago mag-delete
        old_count = destination.execute(
            f"SELECT COUNT(*) FROM {quote_identifier(TABLE)}"
        ).fetchone()[0]

        source_count = 1 + sum(1 for _ in source_rows)

        print(f"\nRecords sa destination ngayon: {old_count}")
        print(f"Records na ililipat mula zear.db: {source_count}")
        print("\nBABALA: Papalitan ang lahat ng records sa destination.")

        answer = input(
            "\nI-type ang REPLACE para ituloy: "
        ).strip()

        if answer != "REPLACE":
            print("Kinansela. Walang binagong records.")
            return

        # 5. Simulan ang transaction
        destination.execute("BEGIN IMMEDIATE")
        transaction_started = True

        destination.execute(
            f"DELETE FROM {quote_identifier(TABLE)}"
        )

        placeholders = ", ".join("?" for _ in columns)
        insert_sql = (
            f"INSERT INTO {quote_identifier(TABLE)} "
            f"({quoted_columns}) VALUES ({placeholders})"
        )

        # 6. Insert isa-isa
        inserted = 0

        # Gamitin ulit ang query para magsimula sa unang record
        rows = source.execute(
            f"SELECT {quoted_columns} FROM {quote_identifier(TABLE)}"
        )

        for row in rows:
            destination.execute(insert_sql, row)
            inserted += 1

            if inserted % 500 == 0:
                print(f"Na-insert na: {inserted}")

        # 7. Verify bago mag-commit
        final_count = destination.execute(
            f"SELECT COUNT(*) FROM {quote_identifier(TABLE)}"
        ).fetchone()[0]

        if final_count != inserted:
            raise RuntimeError(
                f"Count mismatch: inserted={inserted}, "
                f"destination={final_count}"
            )

        destination.commit()
        transaction_started = False

        print("\nSUCCESS!")
        print(f"Records na na-insert: {inserted}")
        print(f"Records sa destination: {final_count}")
        print("Backup file:", backup_path)

    except Exception as error:
        if destination is not None and transaction_started:
            destination.rollback()

        print("\nFAILED:", error)
        print("Kung nagsimula ang transaction, ni-rollback ang mga pagbabago.")

    finally:
        if source is not None:
            source.close()
        if destination is not None:
            destination.close()

    input("\nPress Enter para lumabas...")


if __name__ == "__main__":
    main()
