import os
import sys
import shutil
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_host_entry():
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    hostname_entry = "127.0.0.1    Pyzar"

    try:
        with open(hosts_path, "r+") as f:
            lines = f.readlines()
            if not any("Pyzar" in line for line in lines):
                f.write("\n" + hostname_entry + "\n")
                print("✔ Added 'Pyzar' to hosts file.")
            else:
                print("✔ 'Pyzar' already exists in hosts.")
    except PermissionError:
        print("❌ Admin rights required to modify hosts file.")

def get_appdata_path():
    return os.path.join(os.environ.get("LOCALAPPDATA", "."), "PyZar")

def ensure_db_folder():
    appdata_dir = get_appdata_path()
    db_path = os.path.join(appdata_dir, "app.db")

    if not os.path.exists(appdata_dir):
        os.makedirs(appdata_dir, exist_ok=True)

    if not os.path.exists(db_path):
        # Use the bundled db as source
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = os.path.dirname(__file__)
        bundled_db = os.path.join(bundle_dir, "app.db")
        if os.path.exists(bundled_db):
            shutil.copy(bundled_db, db_path)

    # Hosts update check on first run
    if is_admin():
        add_host_entry()
    else:
        # print("⚠️ To access via 'http://Pyzar', run this app as Administrator once.")
        print("")

    return db_path

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{ensure_db_folder()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'asdddasfsaedasd'



'''
pyinstaller --onefile --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "app.db;." run.py
'''

