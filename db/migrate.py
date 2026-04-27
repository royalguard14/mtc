# import pandas as pd
# import sqlite3
# from datetime import datetime

# # === CONFIG ===
# EXCEL_FILE = "Criminal Case.xlsx"
# SHEET_NAME = "Sheet9"
# DB_FILE = "zear.db"

# COURT_ID_FIXED = 2088
# DEFAULT_CREATEBY = "BCC1"
# DEFAULT_MODIFYBY = "BCC1"

# # === LOAD EXCEL ===
# df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
# df.columns = df.columns.str.strip()

# # === CONNECT DB ===
# conn = sqlite3.connect(DB_FILE)
# cursor = conn.cursor()

# # === HELPERS ===
# def format_code(value, default="00000"):
#     if pd.isna(value) or value == "":
#         return default
#     try:
#         return str(int(float(value))).zfill(5)
#     except:
#         return default

# def format_text(value, default=""):
#     if pd.isna(value) or value is None:
#         return default
#     return str(value)

# def format_date(value):
#     if pd.isna(value) or value == "":
#         return None
#     try:
#         return pd.to_datetime(value).strftime("%Y-%m-%d")
#     except:
#         return None

# # === CREATEDT RULE ===
# def get_created_dt(value):
#     if pd.notna(value) and value != "":
#         try:
#             return pd.to_datetime(value).strftime("%Y-%m-%dT%H:%M:%S")
#         except:
#             pass
#     return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# # === MODIFYDT RULE (ALWAYS NOW) ===
# def get_modify_dt():
#     return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# # === CONFIRM DELETE ===
# confirm = input("⚠️ This will DELETE all records in ctms1000. Continue? (y/n): ")
# if confirm.lower() != 'y':
#     print("❌ Cancelled.")
#     exit()

# cursor.execute("DELETE FROM ctms1000")
# conn.commit()
# print("✅ Table cleaned.")

# # === COUNTERS ===
# success = 0
# errors = 0

# # === INSERT LOOP ===
# for index, row in df.iterrows():
#     try:

#         if pd.isna(row.get("CASEID")) or pd.isna(row.get("CASENUM")):
#             continue

#         created_dt = get_created_dt(row.get("CREATEDT"))
#         modify_dt = get_modify_dt()

#         data = (
#             int(row["CASEID"]),
#             COURT_ID_FIXED,

#             format_code(row.get("NATURECODE")),
#             format_code(row.get("CATEGORY"), "00005"),

#             format_text(row.get("CASENUM")),
#             format_text(row.get("CASETITLE")).upper(),

#             format_date(row.get("DTFILED")),
#             format_date(row.get("DTRECEIVED")),
#             format_date(row.get("DTTRANSFER")),

#             row.get("TRANSFER"),

#             format_text(row.get("CASETYPE"), "CR"),

#             format_date(row.get("CLOSEDATE")),

#             format_text(row.get("CLOSETAG")),
#             format_text(row.get("CLOSEDET")),

#             format_text(row.get("NATUREREM")).upper(),

#             float(row.get("IAMOUNT", 0.0) or 0.0),
#             float(row.get("IWEIGHT", 0.0) or 0.0),

#             format_text(row.get("CSTATUS")),

#             format_code(row.get("CSTATUSID")),

#             format_code(row.get("CLOSESTAT"), "10006"),

#             format_text(row.get("CREATEBY"), DEFAULT_CREATEBY),

#             created_dt,

#             format_text(row.get("MODIFYBY"), DEFAULT_MODIFYBY),

#             modify_dt
#         )

#         cursor.execute("""
#             INSERT INTO ctms1000 (
#                 CASEID, COURTID, NATURECODE, CATEGORY, CASENUM, CASETITLE,
#                 DTFILED, DTRECEIVED, DTTRANSFER, TRANSFER, CASETYPE,
#                 CLOSEDATE, CLOSETAG, CLOSEDET, NATUREREM,
#                 IAMOUNT, IWEIGHT, CSTATUS, CSTATUSID, CLOSESTAT,
#                 CREATEBY, CREATEDT, MODIFYBY, MODIFYDT
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, data)

#         success += 1

#     except Exception as e:
#         print(f"❌ Error on row {index}: {e}")
#         errors += 1

# # === SAVE ===
# conn.commit()
# conn.close()

# # === RESULT ===
# print("\n🎉 Migration completed.")
# print(f"✅ Inserted: {success}")
# print(f"❌ Errors: {errors}")


# import sqlite3

# # === DATABASES ===
# ORIGINAL_DB = "original.db"
# ZEAR_DB = "zear.db"

# # === CONNECT BOTH DBs ===
# conn_orig = sqlite3.connect(ORIGINAL_DB)
# conn_zear = sqlite3.connect(ZEAR_DB)

# cur_orig = conn_orig.cursor()
# cur_zear = conn_zear.cursor()

# # === STEP 1: GET ALL CASENUM + CREATEDT FROM ORIGINAL ===
# cur_orig.execute("""
#     SELECT CASENUM, CREATEDT
#     FROM ctms1000
#     WHERE CASENUM IS NOT NULL
# """)

# original_data = cur_orig.fetchall()

# print(f"📦 Found {len(original_data)} records in original.db")

# # === STEP 2: UPDATE ZEAR DB ===
# updated = 0
# not_found = 0

# for casenum, createdt in original_data:
#     if not casenum or not createdt:
#         continue

#     cur_zear.execute("""
#         UPDATE ctms1000
#         SET CREATEDT = ?
#         WHERE CASENUM = ?
#     """, (createdt, casenum))

#     if cur_zear.rowcount > 0:
#         updated += 1
#     else:
#         not_found += 1

# # === SAVE ===
# conn_zear.commit()

# # === CLOSE CONNECTIONS ===
# conn_orig.close()
# conn_zear.close()

# # === RESULT ===
# print("\n🎉 Sync completed.")
# print(f"✅ Updated: {updated}")
# print(f"⚠️ Not found: {not_found}")



import sqlite3
import random
from datetime import datetime, timedelta

DB_FILE = "zear.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# === WORKING DAYS RANGE ===
start_date = datetime(2026, 4, 1)
end_date = datetime(2026, 4, 27)

# === GET ALL CASEIDS ===
cursor.execute("SELECT CASEID FROM ctms1000")
rows = cursor.fetchall()

print(f"📦 Total records: {len(rows)}")

# === GENERATE VALID WORKDAY LIST (NO WEEKENDS) ===
valid_dates = []
current = start_date

while current <= end_date:
    if current.weekday() < 5:  # Mon-Fri only
        valid_dates.append(current)
    current += timedelta(days=1)

# === RANDOM DATETIME GENERATOR ===
def random_work_datetime(base_date):
    hour = random.randint(8, 16)  # 8 AM - 4 PM start hours
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    dt = base_date.replace(hour=hour, minute=minute, second=second)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

# === UPDATE LOOP ===
for i, (caseid,) in enumerate(rows):
    try:
        # pick random valid workday
        base_date = random.choice(valid_dates)

        modifydt = random_work_datetime(base_date)

        cursor.execute("""
            UPDATE ctms1000
            SET MODIFYDT = ?
            WHERE CASEID = ?
        """, (modifydt, caseid))

    except Exception as e:
        print(f"❌ Error CASEID {caseid}: {e}")

conn.commit()
conn.close()

print("🎉 MODIFYDT randomization completed.")