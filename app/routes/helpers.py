import os
from dbfread import DBF
from sqlalchemy.exc import SQLAlchemyError

from app import db

from app.models import (
    Setting,  # your existing model
    SettingsB, SettingsCTMS,

    CTMS1000, CTMS2100, CTMS2310, CTMS2320,
    CTMS3100, CTMS3200, CTMS4000, CTMS4100,
    TCOURT, TREGION
)

# =========================
# SETTINGS (your existing)
# =========================

def get_all_settings(as_dict=True):
    settings = Setting.query.all()
    if as_dict:
        return {s.function_desc: s.function for s in settings}
    return settings


# =========================
# MODEL MAPPING
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
# VALUE CONVERSION
# =========================

def _convert_value(field, value):
    if value is None:
        return None

    if field.type == 'L':  # Logical
        return 1 if value in (True, 'T', 't', 'Y', 'y') else 0

    if field.type in ('D', 'T'):  # Date / DateTime
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    return value


# =========================
# GENERIC DBF IMPORTER
# =========================

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


# =========================
# AUTO IMPORT ALL DBF FILES
# =========================

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