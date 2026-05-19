from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash
from flask_login import login_required
from app import db
from datetime import datetime, timedelta
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app.routes.decorators import require_module
from app.models import ScheduleMaster, Cases, CTMS1000
from datetime import datetime
from sqlalchemy import cast, Integer, func
import requests
import json



schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')

GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw2My5Z1KySGX-7WwFb9i-JMh7l6e7oDX-xdmbHzrEgOGpEQ1kSALIgal6zmP5kLFBW/exec"

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



@schedule_bp.route('/mark-done', methods=['POST'])
@login_required
def mark_done():

    data = request.get_json()
    schedule_id = data.get('id')

    schedule = ScheduleMaster.query.get(schedule_id)

    if not schedule:
        return jsonify({
            "status": "error",
            "message": "Schedule not found"
        }), 404

    try:
        schedule.Status = "DONE"
        db.session.commit()
        sync_to_google_sheet(schedule)
        flash('Hearing Success.', 'success')


        return jsonify({
            "status": "success",
            "message": "Marked as DONE"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



@schedule_bp.route('/create', methods=['POST'])
@login_required
def create_schedule():

    data = request.get_json()


    try:
        # =========================
        # DATE FORMAT
        # Input:  2026-08-11
        # Output: 08/11/2026
        # =========================
        date_str = data.get("Date")
        formatted_date = ""

        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%m/%d/%Y")

        # =========================
        # TIME FORMAT
        # Input:  13:00
        # Output: 01:00 PM
        # =========================
        time_str = data.get("Time_Start")
        formatted_time = ""

        if time_str:
            time_obj = datetime.strptime(time_str, "%H:%M")
            formatted_time = time_obj.strftime("%I:%M %p")

        # =========================
        # CREATE RECORD
        # =========================
        new_sched = ScheduleMaster(
            Date=formatted_date,
            Time_Start=formatted_time,
            Case_Type=data.get("Case_Type"),
            Case_Number=data.get("Case_Number"),
            Title=data.get("Title"),
            Status="",
            Notes=data.get("Notes") or ""
        )

        db.session.add(new_sched)
        db.session.commit()

        # =========================
        # AUTO SYNC TO GOOGLE SHEETS
        # =========================
        sync_to_google_sheet(new_sched)

        return jsonify({
            "status": "success",
            "message": "Schedule created successfully"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@schedule_bp.route('/update', methods=['POST'])
@login_required
def update_schedule():

    data = request.get_json()



    sched = ScheduleMaster.query.get(data.get("id"))

    if not sched:
        return jsonify({
            "status": "error",
            "message": "Schedule not found"
        }), 404

    try:
        # -------------------
        # DATE (YYYY-MM-DD → MM/DD/YYYY)
        # -------------------
        date_str = data.get("Date")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%m/%d/%Y")

        # -------------------
        # TIME (HH:MM → 12-hour AM/PM)
        # -------------------
        time_str = data.get("Time_Start")  # "13:00"
        time_obj = datetime.strptime(time_str, "%H:%M")
        formatted_time = time_obj.strftime("%I:%M %p")  # "01:00 PM"

        # -------------------
        # UPDATE FIELDS
        # -------------------
        sched.Date = formatted_date
        sched.Time_Start = formatted_time
        sched.Case_Type = data.get("Case_Type")
        sched.Case_Number = data.get("Case_Number")
        sched.Title = data.get("Title")
        sched.Notes = data.get("Notes")


        db.session.commit()

        # =========================
        # AUTO SYNC TO GOOGLE SHEETS
        # =========================
        sync_to_google_sheet(sched)

        return jsonify({
            "status": "success",
            "message": "Schedule updated successfully"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# GOOGLE SHEET UPSERT (SCHEDULE MASTER)
# =========================
def sync_to_google_sheet(schedule):

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
            timeout=10
        )

        print("GOOGLE SYNC RESPONSE:", response.text)

    except Exception as e:
        print("Google Sync Error:", str(e))


@schedule_bp.route('/court/api/<case_type>')
@login_required
def court_api(case_type):
    """
    Returns records depending on selected Case Type.

    Example URLs:
    /schedule/court/api/CRIMINAL CASE
    /schedule/court/api/CIVIL CASE
    /schedule/court/api/SMALL CLAIMS CASE
    """

    case_type = case_type.strip().upper()

    # =========================
    # CRIMINAL CASE -> case_number starts with CTMS.1000
    # =========================
    if case_type == "CRIMINAL CASE":
        records = (
            CTMS1000.query
            .order_by(CTMS1000.CASENUM.desc())
            .all()
        )

        return jsonify([
            {
                "Case_Number": r.CASENUM,
                "Title": r.CASETITLE
            }
            for r in records
        ])

    # =========================
    # CIVIL CASE
    # =========================
    elif case_type == "CIVIL CASE":
        CourtRecordsCivil = (
                    Cases.query
                    .filter(func.lower(Cases.case_type) == "civil case")
                    .order_by(Cases.case_number.desc())
                    .all()
                )

        return jsonify([
            {
                
                "Case_Number": r.case_number,
                "Title": r.title
            }
            for r in CourtRecordsCivil
        ])

    # =========================
    # SMALL CLAIMS CASE
    # =========================
    elif case_type == "SMALL CLAIMS CASE":
        CourtRecordsSclaims = (
        Cases.query
        .filter(func.lower(Cases.case_type) == "smallclaims")
        .order_by(
            cast(
                func.substr(
                    Cases.case_number,
                    4,
                    func.instr(
                        func.substr(Cases.case_number, 4),
                        "-"
                    ) - 1
                ),
                Integer
            ).desc()
        )
        .all()
    )

        return jsonify([
            {
               
                "Case_Number": r.case_number,
                "Title": r.title
            }
            for r in CourtRecordsSclaims
        ])


    # =========================
    # COUPLE
    # =========================
    elif case_type == "COUPLE":
        couple = (
                    CivilWedding.query
                    .order_by(CivilWedding.id.desc())
                    .all()
                )

        return jsonify([
            {
                
                "Case_Number": r.case_number,
                "Title": r.title
            }
            for r in couple
        ])      


    # =========================
    # INVALID TYPE
    # =========================
    return jsonify({
        "status": "error",
        "message": f"Invalid case type: {case_type}"
    }), 400