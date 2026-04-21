import os

# =========================
# FILE PATHS
# =========================
DB_DIR = r"C:\Users\Supreme Court\Desktop\New folder"   # 🔁 CHANGE THIS if needed

db1 = os.path.join(DB_DIR, "combined1.db")
db2 = os.path.join(DB_DIR, "combined2.db")

# =========================
# SAFETY CHECKS
# =========================
if not os.path.exists(db2):
    raise FileNotFoundError("combined2.db not found. Cannot proceed.")

# =========================
# DELETE combined1.db
# =========================
if os.path.exists(db1):
    try:
        os.remove(db1)
        print("✔ Deleted combined1.db")
    except Exception as e:
        print(f"❌ Failed to delete combined1.db: {e}")
        exit()

# =========================
# RENAME combine2.db → combined1.db
# =========================
try:
    os.rename(db2, db1)
    print("✔ Renamed combine2.db → combined1.db")
except Exception as e:
    print(f"❌ Failed to rename file: {e}")
    exit()

print("✅ Database swap completed successfully!")