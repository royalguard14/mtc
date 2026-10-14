
import sqlite3
from pathlib import Path
from dbfread import DBF

SOURCE_DB = Path(r"D:\PyZar\forCompare\zear.db")
DBF_FOLDER = Path(r"C:\CTMS\dbf")

TABLES = {
    "ctms1000": "ctms1000.DBF",
    "ctms4000": "ctms4000.DBF",
    "ctms4100": "ctms4100.DBF",
}


def main():
    if not SOURCE_DB.exists():
        print(f"ERROR: Source not found: {SOURCE_DB}")
        return

    print("=" * 65)
    print(" CTMS TRANSFER - FIELD VALIDATION")
    print("=" * 65)

    with sqlite3.connect(
        f"file:{SOURCE_DB.as_posix()}?mode=ro", uri=True
    ) as conn:

        source_tables = {
            row[0].lower(): row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        for table, filename in TABLES.items():
            destination = DBF_FOLDER / filename

            print(f"\n{'-' * 65}")
            print(f"TABLE: {table}")

            if table not in source_tables:
                print("SOURCE: MISSING TABLE")
                continue

            if not destination.exists():
                print(f"DESTINATION: MISSING FILE: {destination}")
                continue

            source_name = source_tables[table]

            source_columns = [
                row[1] for row in conn.execute(
                    f'PRAGMA table_info("{source_name}")'
                )
            ]

            dbf = DBF(
                str(destination),
                load=False,
                char_decode_errors="replace",
            )

            dest_columns = list(dbf.field_names)

            source_set = {c.upper() for c in source_columns}
            dest_set = {c.upper() for c in dest_columns}

            source_count = conn.execute(
                f'SELECT COUNT(*) FROM "{source_name}"'
            ).fetchone()[0]

            dest_count = sum(1 for _ in dbf)

            print(f"Source records:      {source_count:,}")
            print(f"Destination records: {dest_count:,}")
            print(f"Source fields:      {len(source_columns)}")
            print(f"Destination fields: {len(dest_columns)}")

            missing_in_dbf = sorted(source_set - dest_set)
            extra_in_dbf = sorted(dest_set - source_set)

            if not missing_in_dbf and not extra_in_dbf:
                print("FIELD NAMES: MATCH")
            else:
                print("FIELD NAMES: DIFFERENT")
                if missing_in_dbf:
                    print("Fields missing in DBF:", missing_in_dbf)
                if extra_in_dbf:
                    print("Extra fields in DBF:", extra_in_dbf)

            print("\nDestination DBF field definitions:")
            for field in dbf.fields:
                print(
                    f"  {field.name:<15} "
                    f"type={field.type} "
                    f"length={field.length} "
                    f"decimals={getattr(field, 'decimal_count', 0)}"
                )

    print("\nValidation completed. No files were modified.")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
