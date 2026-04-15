import os
import sqlite3
import dbf
from datetime import datetime
from dbfread import DBF
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import (
    Setting,
    SettingsB,
    SettingsCTMS,
    CTMS1000, CTMS2100, CTMS2310, CTMS2320,
    CTMS3100, CTMS3200, CTMS4000, CTMS4100,
    TCOURT, TREGION
)

# =========================
# SETTINGS
# =========================

def get_all_settings(as_dict=True):
    settings = Setting.query.all()
    if as_dict:
        return {s.function_desc: s.function for s in settings}
    return settings


# =========================
# MODEL MAP (DBF IMPORT)
# =========================

MODEL_MAP = {
    "settingsb": SettingsB,
    "settingsctms": SettingsCTMS,
    "ctms1000": CTMS1000,
    "ctms2100": CTMS2100,
    "ctms2310": CTMS2310,
    "ctms2320": CTMS2320,
    "ctms3100": CTMS3100,
    "ctms3200": CTMS3200,
    "ctms4000": CTMS4000,
    "ctms4100": CTMS4100,
    "tcourt": TCOURT,
    "tregion": TREGION,
}


# =========================
# DBF IMPORT (ONE TIME LOAD)
# =========================

def _convert_value(field, value):
    if value is None:
        return None

    if field.type == 'L':
        return 1 if value in (True, 'T', 't', 'Y', 'y') else 0

    if field.type in ('D', 'T'):
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    return value


def import_dbf_to_model(dbf_path, model):
    try:
        table = DBF(dbf_path, load=True)
        fields = table.fields

        for record in table:
            data = {}

            for field in fields:
                data[field.name] = _convert_value(field, record.get(field.name))

            obj = model(**data)
            db.session.add(obj)

        db.session.commit()
        print(f"✅ Imported: {dbf_path} → {model.__tablename__}")

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ DB ERROR: {e}")

    except Exception as e:
        print(f"❌ ERROR: {e}")


def import_all_dbf(folder_path):
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".dbf"):
            continue

        table_name = os.path.splitext(filename)[0].lower()
        dbf_path = os.path.join(folder_path, filename)

        model = MODEL_MAP.get(table_name)

        if not model:
            print(f"⚠️ No model mapped for: {table_name}")
            continue

        print(f"➡️ Importing {table_name}")
        import_dbf_to_model(dbf_path, model)


# =========================
# SYSTEM HELPERS
# =========================

CURRENT_USER = "BCC1"


def get_now():
    return datetime.now().isoformat(timespec='microseconds')


def touch_case(case_id):
    case = CTMS1000.query.get(case_id)
    if case:
        case.MODIFYDT = get_now()
        case.MODIFYBY = CURRENT_USER


# =========================
# DBF SYNC CONFIG
# =========================

SQLITE_DB = r"D:\PyZar\app1.db"
DBF_FOLDER = r"C:\CTMS\dbf"

TARGET_TABLES = ["ctms1000", "ctms4000", "ctms4100"]

PRIMARY_KEYS = {
    "ctms1000": "CASEID",
    "ctms4000": "PERSONID",
    "ctms4100": "PARTYID",
    "ctms9000": "CASEID"
}


# =========================
# SYNC HELPERS
# =========================

def get_sqlite_map(conn, table):
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    rows = cur.fetchall()
    return {r[1].upper(): r[1] for r in rows}


def parse_dt(val):
    if not val:
        return datetime.min
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("T", " "))
    except:
        return datetime.min


def safe_get(rec, field):
    try:
        return getattr(rec, field)
    except:
        return None


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


def get_field_types(dbf_table):
    types = {}
    for f in dbf_table.structure():
        parts = f.split()
        name = parts[0].upper()
        types[name] = parts[1][0]
    return types


def build_index(dbf_table, key):
    index = {}
    for r in dbf_table:
        try:
            index[str(getattr(r, key))] = r
        except:
            pass
    return index


# =========================
# CORE SYNC ENGINE
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

    inserted = updated = unchanged = skipped = 0

    # =========================
    # BUILD DBF INDEX (SAFE VERSION)
    # =========================
    index = {}
    for r in dbf_table:
        try:
            val = getattr(r, key, None)
            if val is not None:
                index[str(val).strip()] = r
        except:
            pass

    for row in rows:
        sqlite_row = dict(zip(sqlite_map.keys(), row))

        pk = sqlite_row.get(key.upper())

        if pk is None:
            skipped += 1
            continue

        pk = str(pk).strip()

        try:
            found = index.get(pk)

            # =========================
            # BUILD FULL ROW
            # =========================
            full_row = {}

            for col in dbf_cols:
                sql_col = sqlite_map.get(col)
                value = sqlite_row.get(sql_col) if sql_col else None
                full_row[col] = convert_value(value, dbf_types.get(col, 'C'))

            # =========================
            # UPDATE
            # =========================
            if found:
                sql_dt = sqlite_row.get("MODIFYDT")
                dbf_dt = safe_get(found, "MODIFYDT")

                should_update = True
                if "MODIFYDT" in dbf_cols:
                    should_update = parse_dt(sql_dt) > parse_dt(dbf_dt)

                if should_update:
                    with found:
                        for k, v in full_row.items():
                            setattr(found, k, v)
                    updated += 1
                else:
                    unchanged += 1

            # =========================
            # INSERT (FIXED - NOW ALWAYS WORKS)
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
# MAIN SYNC CALL
# =========================

def run_dbf_sync():
    conn = sqlite3.connect(SQLITE_DB)

    try:
        print("\n🚀 DBF SYNC START\n")

        for table in TARGET_TABLES:
            sync_table(conn, table)

        print("\n🎉 DBF SYNC COMPLETE")

    finally:
        conn.close()