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

    if field_type.startswith("C"):
        return str(value)

    if field_type == "D":
        if value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        text = str(value).strip()
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
                try:
                    return datetime.strptime(text[:10], fmt).date()
                except ValueError:
                    pass
        raise ValueError(f"Cannot convert {name} to date: {value!r}")

    if field_type.startswith("T"):
        if value == "":
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        text = str(value).strip()
        try:
            # Handles SQLite ISO values such as 2022-05-25T09:17:13.999000.
            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S.%f",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(text[:26], fmt)
                except ValueError:
                    pass
        raise ValueError(f"Cannot convert {name} to datetime: {value!r}")

    if field_type.startswith(("N", "F", "I", "B", "Y")):
        if value == "":
            return None
        if field_type.startswith("I"):
            return int(value)
        return float(value)

    if field_type.startswith("L"):
        if isinstance(value, str):
            return value.strip().upper() in ("Y", "T", "TRUE", "1")
        return bool(value)

    return value

def read_source():
    if not SOURCE.exists():
        raise FileNotFoundError(f"SQLite source not found: {SOURCE}")

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

    return source_data

def make_backup():
    backup_dir = DEST / (
        "backup_before_transfer_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    backup_dir.mkdir()

    for filename in TABLES.values():
        stem = Path(filename).stem.lower()
        for path in DEST.iterdir():
            if path.is_file() and path.stem.lower() == stem:
                shutil.copy2(path, backup_dir / path.name)

    return backup_dir

def restore_backup(backup_dir):
    for backup_file in backup_dir.iterdir():
        if backup_file.is_file():
            shutil.copy2(backup_file, DEST / backup_file.name)

def main():
    for filename in TABLES.values():
        if not (DEST / filename).exists():
            raise FileNotFoundError(f"Destination DBF missing: {DEST / filename}")

    source_data = read_source()

    print("SOURCE RECORD COUNTS")
    for table, (_, rows) in source_data.items():
        print(f"{table}: {len(rows)}")

    tables = {}
    prepared = {}
    backup_dir = None
    write_started = False

    try:
        # Open and validate every destination before any records are changed.
        for table, filename in TABLES.items():
            target = dbf.Table(str(DEST / filename))
            target.open(dbf.READ_WRITE)
            tables[table] = target

            source_columns, rows = source_data[table]
            source_names = {c.upper() for c in source_columns}
            definitions = list(target.structure())
            target_names = {field_name(d) for d in definitions}

            missing = source_names - target_names
            if table == "ctms4100":
                missing -= {"DECIDETYPE", "OTHER_STATUS"}
            if missing:
                raise RuntimeError(
                    f"{table}: source fields not found in DBF: {sorted(missing)}"
                )

            source_index = {
                name.upper(): i for i, name in enumerate(source_columns)
            }
            target_columns = [field_name(d) for d in definitions]

            # Convert ALL rows before zap(). Any conversion error stops safely here.
            converted_rows = []
            for row_number, row in enumerate(rows, start=1):
                values = []
                for definition, name in zip(definitions, target_columns):
                    index = source_index.get(name)
                    value = row[index] if index is not None else None
                    try:
                        converted = convert_value(value, definition)
                    except Exception as exc:
                        raise ValueError(
                            f"{table}, source row {row_number}, field {name}: {exc}"
                        ) from exc

                    # Fail before writing if a character value exceeds its DBF field.
                    parts = definition.split()
                    if (converted is not None and len(parts) > 1
                            and parts[1].upper().startswith("C")):
                        width = int(parts[1].split("(")[1].split(")")[0])
                        if len(str(converted)) > width:
                            raise ValueError(
                                f"{table}, source row {row_number}, field {name}: "
                                f"value length {len(str(converted))} exceeds field width {width}"
                            )
                    values.append(converted)
                converted_rows.append(tuple(values))

            prepared[table] = converted_rows

        print("\nAll field mappings and source values validated.")
        print("No destination records have been changed yet.")
        print("\nWARNING: This replaces destination records.")
        print("Visual FoxPro CDX indexes may need rebuilding before CTMS is used.")
        if input("Type REPLACE to continue: ").strip() != "REPLACE":
            print("Cancelled. Destination records were not changed.")
            return

        backup_dir = make_backup()
        print(f"Backup saved to: {backup_dir}")

        # Only begin destructive changes after every table has validated and backup exists.
        write_started = True
        for table in TABLES:
            target = tables[table]
            rows = prepared[table]
            print(f"\nReplacing {table}...")
            target.zap()
            for row in rows:
                target.append(row)

            actual_count = len(target)
            expected_count = len(rows)
            print(f"Expected: {expected_count}; written: {actual_count}")
            if actual_count != expected_count:
                raise RuntimeError(
                    f"{table}: record count mismatch after transfer"
                )

        print("\nTRANSFER FINISHED.")
        print("Before using CTMS, verify/rebuild the Visual FoxPro CDX indexes.")

    except Exception:
        # Close DBF handles before restoring the backup files.
        for target in tables.values():
            try:
                target.close()
            except Exception:
                pass
        tables.clear()

        if write_started and backup_dir and backup_dir.exists():
            print("\nERROR during transfer. Restoring DBF/CDX/BAK from backup...")
            try:
                restore_backup(backup_dir)
                print("Backup restore completed.")
            except Exception as restore_error:
                print(f"AUTOMATIC RESTORE FAILED: {restore_error}")
                print(f"Manual backup location: {backup_dir}")
        raise

    finally:
        for target in tables.values():
            try:
                target.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
