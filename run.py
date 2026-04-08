import multiprocessing
multiprocessing.freeze_support()
from app.core.firebase_licensing import check_license_flow
from app import create_app

app = create_app()

if not check_license_flow():
    print("🚫 App shutting down due to license validation failure.")
    exit()  
    
if __name__ == "__main__":
    app.run(debug=True)