# import_sched_csv.py
# Location of this file:
# D:\PyZar\db\import_sched_csv.py
#
# Project structure:
# D:\PyZar\
# ├── app\
# │   └── models.py
# └── db\
#     ├── zear.db
#     ├── sched.csv
#     └── import_sched_csv.py

import csv
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
# Add this near the top of your file
import requests


# ==========================================================
# GOOGLE SHEETS WEBHOOK
# ==========================================================
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw2My5Z1KySGX-7WwFb9i-JMh7l6e7oDX-xdmbHzrEgOGpEQ1kSALIgal6zmP5kLFBW/exec"


def sync_to_google_sheet(schedule):
    """
    Send one ScheduleMaster record to Google Sheets using UPSERT.
    """

    payload = {
        "type": "UPSERT",
        "sheet": "Schedule Master",
        "keyColumn": "id",
        "keyValue": schedule.id,
        "data": {
            "id": schedule.id,
            "Date": schedule.Date or "",
            "Time Start": schedule.Time_Start or "",
            "Case Type": schedule.Case_Type or "",
            "Case Number": schedule.Case_Number or "",
            "Title": schedule.Title or "",
            "Status": schedule.Status or "",
            "Notes": schedule.Notes or ""
        }
    }

    try:
        response = requests.post(
            GOOGLE_WEBHOOK_URL,
            json=payload,
            timeout=30
        )

        print(f"📤 Synced ID {schedule.id}: {response.text}")

    except Exception as e:
        print(f"❌ Google Sync Error for ID {schedule.id}: {e}")


# ==========================================================
# ADD PROJECT ROOT TO PYTHON PATH
# This allows importing from D:\PyZar\app\models.py
# ==========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))       # D:\PyZar\db
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)                    # D:\PyZar

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ==========================================================
# IMPORT MODEL
# ==========================================================
from app.models import ScheduleMaster

# ==========================================================
# DATABASE CONFIGURATION
# zear.db is in the same folder as this script
# ==========================================================
DB_PATH = os.path.join(CURRENT_DIR, "zear.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# ==========================================================
# FORMAT DATE
# Input:  2026-08-11
# Output: 08/11/2026
# ==========================================================
def format_date(date_str):
    if not date_str:
        return ""

    date_str = str(date_str).strip()

    # Already MM/DD/YYYY
    try:
        datetime.strptime(date_str, "%m/%d/%Y")
        return date_str
    except:
        pass

    # Convert YYYY-MM-DD
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%m/%d/%Y")
    except:
        return date_str


# ==========================================================
# FORMAT TIME
# Input:  13:00
# Output: 01:00 PM
# ==========================================================
def format_time(time_str):
    if not time_str:
        return ""

    time_str = str(time_str).strip()

    # Already 01:00 PM
    try:
        datetime.strptime(time_str, "%I:%M %p")
        return time_str
    except:
        pass

    # Convert 24-hour format
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%I:%M %p")
    except:
        return time_str


# ==========================================================
# IMPORT CSV TO DATABASE
# ==========================================================
def import_csv(csv_file="sched.csv"):
    csv_path = os.path.join(CURRENT_DIR, csv_file)

    session = Session()
    inserted = 0
    skipped = 0
    inserted_records = []   # store inserted records for Google sync

    try:
        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Skip completely blank rows
                if not any(row.values()):
                    skipped += 1
                    continue

                # Create record
                record = ScheduleMaster(
                    Date=format_date(row.get("Date")),
                    Time_Start=format_time(row.get("Time_Start")),   # note the space
                    Case_Type=(row.get("Case_Type") or "").strip(),
                    Case_Number=(row.get("Case_Number") or "").strip(),
                    Title=(row.get("Title") or "").strip(),
                    Status=(row.get("Status") or "").strip(),
                    Notes=(row.get("Notes") or "").strip(),
                )

                session.add(record)
                inserted_records.append(record)
                inserted += 1

        # ==================================================
        # COMMIT ALL RECORDS FIRST
        # This generates the auto-increment IDs
        # ==================================================
        session.commit()

        # ==================================================
        # SYNC EACH INSERTED RECORD TO GOOGLE SHEETS
        # ==================================================
        for record in inserted_records:
            sync_to_google_sheet(record)

        print("====================================")
        print("✅ Import completed successfully.")
        print(f"Inserted: {inserted}")
        print(f"Skipped: {skipped}")
        print("====================================")

    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")

    except SQLAlchemyError as e:
        session.rollback()
        print(f"❌ Database error: {e}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")

    finally:
        session.close()

# ==========================================================
# RUN SCRIPT
# ==========================================================
if __name__ == "__main__":
    import_csv("sched.csv")