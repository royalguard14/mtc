
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, date
import dbf

SOURCE = Path(r"D:\PyZar\forCompare\zear.db")
DEST = Path(r"C:\CTMS\dbf")

TABLES = {
    "ctms1000": "ctms1000.DBF",
    "ctms4000": "ctms4000.DBF",
    "ctms4100": "ctms4100.DBF",
}

def field_name(definition):
    return definition.split()[0].upper()

def convert_value(value, definition):
    if value is None:
        return None

    parts = definition.split()
    name = parts[0]
    field_type = parts[1].upper() if len(parts) > 1 else ""

    # Character fields
    if field_type.startswith("C"):
        return str(value)

    # Date fields
    if field_type == "D":
        if value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S",
                    "%m/%d/%Y", "%Y%m%d"):
            try:
                return datetime.strptime(text[:19], fmt).date()
            except ValueError:
                pass
        raise ValueError(f"Cannot convert {name} to date: {value!r}")

    # Date/time fields
    if field_type.startswith("T"):
        if value == "":
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        text = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(text[:26], fmt)
            except ValueError:
                pass
        raise ValueError(f"Cannot convert {name} to datetime: {value!r}")

    # Numeric / integer / floating fields
    if field_type.startswith(("N", "F", "I", "B", "Y")):
        if value == "":
            return None
        if field_type.startswith("I"):
            return int(value)
        return float(value) if "." in str(value) else int(value)

    # Logical fields
    if field_type.startswith("L"):
        if isinstance(value, str):
            return value.strip().upper() in ("Y", "T", "TRUE", "1")
        return bool(value)

    return value

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"SQLite source not found: {SOURCE}")

    for filename in TABLES.values():
        if not (DEST / filename).exists():
            raise FileNotFoundError(f"Destination DBF missing: {DEST / filename}")

    # Read source data first, without modifying any destination.
    source_data = {}
    with sqlite3.connect(
        f"file:{SOURCE.as_posix()}?mode=ro", uri=True
    ) as conn:
        available = {
            row[0].lower(): row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        for table in TABLES:
            if table not in available:
                raise RuntimeError(f"Source table missing: {table}")

            actual = available[table]
            columns = [
                row[1] for row in conn.execute(
                    f'PRAGMA table_info("{actual}")'
                )
            ]
            rows = conn.execute(
                f'SELECT * FROM "{actual}"'
            ).fetchall()
            source_data[table] = (columns, rows)

    print("SOURCE RECORD COUNTS")
    for table, (_, rows) in source_data.items():
        print(f"{table}: {len(rows)}")

    # Open destination tables and validate field mapping.
    tables = {}
    try:
        for table, filename in TABLES.items():
            path = DEST / filename
            target = dbf.Table(str(path))
            target.open(dbf.READ_WRITE)
            tables[table] = target

            source_columns, _ = source_data[table]
            source_names = {c.upper() for c in source_columns}
            target_defs = list(target.structure())
            target_names = {field_name(d) for d in target_defs}

            missing = source_names - target_names
            if table == "ctms4100":
                allowed = {"DECIDETYPE", "OTHER_STATUS"}
                missing -= allowed

            if missing:
                raise RuntimeError(
                    f"{table}: source fields not found in DBF: "
                    f"{sorted(missing)}"
                )

        print("\nAll destination tables and field mappings checked.")

        # Require a second explicit confirmation before destructive writes.
        print("\nWARNING: This will replace all existing records.")
        print("CDX index files may become stale after direct Python writes.")
        print("Do not use CTMS until the indexes have been verified/rebuilt.")
        if input("Type REPLACE to continue: ").strip() != "REPLACE":
            print("Cancelled. Destination records were not changed.")
            return

        # Back up all related files before the first write.
        backup_dir = DEST / (
            "backup_before_transfer_" +
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        backup_dir.mkdir()

        for filename in TABLES.values():
            stem = Path(filename).stem.lower()
            for path in DEST.iterdir():
                if path.is_file() and path.stem.lower() == stem:
                    shutil.copy2(path, backup_dir / path.name)

        print(f"Backup saved to: {backup_dir}")

        # Replace records using fields that exist in each destination DBF.
        for table, filename in TABLES.items():
            target = tables[table]
            source_columns, rows = source_data[table]
            source_index = {
                name.upper(): i for i, name in enumerate(source_columns)
            }
            definitions = list(target.structure())
            target_columns = [field_name(d) for d in definitions]

            print(f"\nReplacing {table}...")
            target.zap()

            for row in rows:
                values = []
                for definition, name in zip(definitions, target_columns):
                    index = source_index.get(name)
                    value = row[index] if index is not None else None
                    values.append(convert_value(value, definition))

                target.append(tuple(values))

            actual_count = len(target)
            expected_count = len(rows)
            print(f"Expected: {expected_count}; written: {actual_count}")

            if actual_count != expected_count:
                raise RuntimeError(
                    f"{table}: record count mismatch after transfer"
                )

        print("\nTRANSFER FINISHED.")
        print("Verify the DBF/CDX indexes before reopening CTMS.")

    finally:
        for target in tables.values():
            try:
                target.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
