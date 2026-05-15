from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash
from flask_login import login_required
from app import db
from datetime import datetime, timedelta
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app.routes.decorators import require_module
from app.models import ScheduleMaster
from datetime import datetime
from sqlalchemy import func


schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')


@schedule_bp.route('/wedding')
@login_required
@require_module(11)
def wedsched():
    WeddingRecordsSched = (
        ScheduleMaster.query
        .filter(func.lower(ScheduleMaster.Case_Type) == "wedding")
        .all()
    )

    WeddingRecordsSched.sort(
        key=lambda x: (
            datetime.strptime(x.Date, "%m/%d/%Y") if x.Date else datetime.min,
            x.Time_Start or ""
        )
    )

    return render_template(
        "schedules/wedding.html",
        WeddingRecordsSched=WeddingRecordsSched,
        now=datetime.now
    )

@schedule_bp.route('/court')
@login_required
@require_module(12)
def courtsched():


    CourtRecordsSched = (
        ScheduleMaster.query
        .filter(func.lower(ScheduleMaster.Case_Type) != "wedding")
        .all()
    )

    CourtRecordsSched.sort(
    key=lambda x: (
        datetime.strptime(x.Date, "%m/%d/%Y") if x.Date else datetime.min,
        x.Time_Start or ""
    )
    )

    return render_template(
    "schedules/other_cases.html",
    CourtRecordsSched=CourtRecordsSched,
    now=datetime.now
    )




@schedule_bp.route('/api/schedule-master-sync')
def api_schedule_master_sync():

    # EXACT Google Sheet headers
    fields = [
        "id",
        "Date",
        "Time Start",
        "Case Type",
        "Case Number",
        "Title",
        "Status",
        "Notes"
    ]

    # Query your SQLAlchemy model
    rows = ScheduleMaster.query.order_by(ScheduleMaster.id).all()

    # Convert DB rows into raw row lists
    data = []
    for r in rows:
        data.append([
            r.id,
            r.Date,
            r.Time_Start,
            r.Case_Type,
            r.Case_Number,
            r.Title,
            r.Status,
            r.Notes
        ])

    # Payload expected by your Google Apps Script doPost()
    payload = {
        "type": "FULL_SYNC",
        "headers": fields,
        "data": data
    }

    try:
        response = requests.post(
            GOOGLE_WEBHOOK_URL,   # Your deployed Apps Script URL
            json=payload,
            timeout=60
        )

        return jsonify({
            "status": "success",
            "google_response": response.text
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



# IMPORT "Schedule Master" FROM GOOGLE SHEET TO DATABASE
# Add this route to your Flask application.

import requests
from flask import jsonify

# Google Apps Script URL that returns JSON from Schedule Master
SCHEDULE_MASTER_API_URL = (
    "https://script.google.com/macros/s/AKfycbxfsQOvTi5ZP51bKn_N8RqX3K39Mufrwh9w2AEG69LI0lJBS_0Erpu8Fhfg9V_oubtw/exec?api=schedule"
)


@schedule_bp.route('/api/import-schedule-master')
def import_schedule_master():
    try:
        # Fetch data from Google Sheet JSON API
        response = requests.get(SCHEDULE_MASTER_API_URL, timeout=60)
        response.raise_for_status()
        records = response.json()

        # Remove old records
        ScheduleMaster.query.delete()

        count = 0

        for row in records:
            # Safe handling for the "id" column
            raw_id = row.get('id')

            try:
                record_id = int(raw_id)
            except (TypeError, ValueError):
                # If the value is not a valid integer
                # (e.g. "12/31/1899"), let the database auto-generate the ID
                record_id = None

            record = ScheduleMaster(
                id=record_id,
                Date=row.get('Date'),
                Time_Start=row.get('Time Start'),
                Case_Type=row.get('Case Type'),
                Case_Number=row.get('Case Number'),
                Title=row.get('Title'),
                Status=row.get('Status'),
                Notes=row.get('Notes')
            )

            db.session.add(record)
            count += 1

        db.session.commit()

        return jsonify({
            "status": "success",
            "imported": count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500