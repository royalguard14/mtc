from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash
from flask_login import login_required
from app import db
from datetime import datetime, timedelta
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app.routes.decorators import require_module
from app.models import CivilWedding
from datetime import datetime
from sqlalchemy import cast, Integer, func
import requests
import json


wedding_bp = Blueprint('wedding', __name__, url_prefix='/wedding')
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw2My5Z1KySGX-7WwFb9i-JMh7l6e7oDX-xdmbHzrEgOGpEQ1kSALIgal6zmP5kLFBW/exec"

def safe_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


@wedding_bp.route('/')
@login_required
@require_module(17)
def wed_index():

    WeddingRecords = CivilWedding.query.all()

    return render_template(
        "wedding/index.html",
        WeddingRecords=WeddingRecords,
    )

@wedding_bp.route('/create', methods=['POST'])
@login_required
def create_wedding():

    data = request.get_json()

    try:
        new_wed = CivilWedding(
            groom=data.get("groom", ""),
            bride=data.get("bride", ""),
			bday_groom=safe_date(data.get("bday_groom")),
			bday_bride=safe_date(data.get("bday_bride")),
            jeeps_or=data.get("jeps_or") or "",
            contact_no=data.get("contact_no") or "",
            register_no="",
            claim_by=[]
        )

        db.session.add(new_wed)
        db.session.commit()
        sync_civil_wedding_to_google_sheet(new_wed)

        return jsonify({
            "status": "success",
            "message": "Couple added successfully"
        })

    except Exception as e:
        db.session.rollback()
        print("🔥 ERROR:", str(e))  # ADD THIS
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@wedding_bp.route('/update', methods=['POST'])
@login_required
def update_wedding():

    data = request.get_json()

    try:
        # Convert string ID to integer
        wedding_id = int(data.get("id"))

        # Find record
        wed = CivilWedding.query.get(wedding_id)

        if not wed:
            return jsonify({
                "status": "error",
                "message": "Record not found"
            }), 404

        # Convert birthday strings to Python date objects
        bday_groom = None
        if data.get("bday_groom"):
            bday_groom = datetime.strptime(
                data.get("bday_groom"),
                "%Y-%m-%d"
            ).date()

        bday_bride = None
        if data.get("bday_bride"):
            bday_bride = datetime.strptime(
                data.get("bday_bride"),
                "%Y-%m-%d"
            ).date()

        # Update fields
        wed.register_no = data.get("register_no") or ""
        wed.groom = data.get("groom") or ""
        wed.bride = data.get("bride") or ""
        wed.bday_groom = bday_groom
        wed.bday_bride = bday_bride
        wed.contact_no = data.get("contact_no") or ""
        wed.jeeps_or = data.get("jeps_or") or ""

        # Save
        db.session.commit()
        sync_civil_wedding_to_google_sheet(wed)

        return jsonify({
            "status": "success",
            "message": "Wedding record updated successfully"
        })

    except Exception as e:
        db.session.rollback()
        print("UPDATE ERROR:", str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# GOOGLE SHEET UPSERT (CIVIL WEDDING)
# =========================
def sync_civil_wedding_to_google_sheet(wed):

    # Convert date objects to strings for Google Sheets
    bday_groom = wed.bday_groom.strftime("%m/%d/%Y") if wed.bday_groom else ""
    bday_bride = wed.bday_bride.strftime("%m/%d/%Y") if wed.bday_bride else ""

    payload = {
        "type": "UPSERT",
        "sheet": "Civil Wedding",
        "keyColumn": "id",
        "keyValue": wed.id,
        "data": {
            "id": wed.id,
            "groom": wed.groom or "",
            "bride": wed.bride or "",
            "bday_groom": bday_groom,
            "bday_bride": bday_bride,
            "schedule_id": wed.schedule_id or "",
            "jeeps_or": wed.jeeps_or or "",
            "contact_no": wed.contact_no or "",
            "register_no": wed.register_no or "",
            "claim_by": json.dumps(wed.claim_by or [])
        }
    }


    try:
        response = requests.post(
            GOOGLE_WEBHOOK_URL,
            json=payload,
            timeout=10
        )

        print("GOOGLE SYNC RESPONSE:", response.text)

    except Exception as e:
        print("Google Sync Error:", str(e))