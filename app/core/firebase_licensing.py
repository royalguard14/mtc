import os
import socket
import firebase_admin
from firebase_admin import credentials, firestore
import uuid

# --- Initialization ---
def init_firebase():
    if not firebase_admin._apps:
        primary = "app/core/pyzar-6b377-firebase-adminsdk-fbsvc-5fca637c0f.json"
        fallback = "app/core/pyzar-6b377-firebase-adminsdk-fbsvc-4bae0de02c.json"

        cred_path = None

        if os.path.exists(primary):
            cred_path = primary
        elif os.path.exists(fallback):
            cred_path = fallback
        else:
            raise FileNotFoundError("No Firebase credential file found.")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        
init_firebase()
db = firestore.client()


# --- Device ID (used for binding) ---
def get_device_id():
    #return socket.gethostname()  # or use `hex(uuid.getnode())` for MAC address
    mac = uuid.getnode()
    return ':'.join(f'{(mac >> ele) & 0xff:02x}' for ele in range(40, -1, -8))


# --- Local License Cache (.verified) ---
def mark_verified(serial_key):
    with open(".verified", "w") as f:
        f.write(serial_key)

def get_local_serial_key():
    if not os.path.exists(".verified"):
        return None
    with open(".verified", "r") as f:
        return f.read().strip()


# --- Check License Validity in Firestore ---
def is_license_still_valid(serial_key):
    doc_ref = db.collection("licenses").document(serial_key)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    data = doc.to_dict()
    return (
        data.get("valid") is True and
        data.get("bound_to") == get_device_id()
    )


# --- First-Time or Manual Validation ---
def validate_serial_key(serial_key):
    doc_ref = db.collection("licenses").document(serial_key)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    data = doc.to_dict()
    current_device = get_device_id()

    # ❌ License used on another device
    if data.get("used") and data.get("bound_to") != current_device:
        print("🚫 License is already used on another device.")
        return False

    # ✅ First-time use
    if data.get("valid") and not data.get("used"):
        doc_ref.update({
            "used": True,
            "bound_to": current_device
        })
        return True

    # ✅ Already used, but on this device
    if data.get("bound_to") == current_device and data.get("valid"):
        return True

    return False


# --- Main Entry Point ---
def check_license_flow():
    serial_key = get_local_serial_key()

    if serial_key and is_license_still_valid(serial_key):
        return True

    print("🔐 This application requires license activation.")
    serial_key = input("🔑 Enter your license key: ").strip()

    if validate_serial_key(serial_key):
        mark_verified(serial_key)
        print("✅ License validated and stored.")
        return True
    else:
        print("❌ Invalid or already used license key.")
        return False
