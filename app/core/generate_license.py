import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import argparse

# === Setup Firebase ===
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("app/core/pyzar-6b377-firebase-adminsdk-fbsvc-4bae0de02c.json")  # Adjust path if needed
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# === Generate a random license key ===
def generate_key(length=6, groups=2):
    return '-'.join(
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        for _ in range(groups)
    )

# === Insert license into Firestore ===
def create_license(client_name, note=""):
    key = generate_key()
    data = {
        "valid": True,
        "used": False,
        "client": client_name,
        "note": note,
        "created_at": datetime.utcnow().isoformat(),
    }
    db.collection("licenses").document(key).set(data)
    return key

# === Command line interface ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Firebase license keys.")
    parser.add_argument("client", help="Client name or ID")
    parser.add_argument("--note", help="Optional note (e.g., reseller, purpose)", default="")

    args = parser.parse_args()
    license_key = create_license(args.client, args.note)

    print(f"✅ License key created for {args.client}: {license_key}")


'''
python app/core/generate_license.py "Zear Corporation" --note "Trial key for dev test"

'''