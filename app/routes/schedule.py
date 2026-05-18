from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash
from flask_login import login_required
from app import db
from datetime import datetime, timedelta
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app.routes.decorators import require_module
from app.models import ScheduleMaster, Cases
from datetime import datetime
from sqlalchemy import func
import requests



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

    # DATE
    date_str = data.get("Date")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%m/%d/%Y")

    # TIME (FIX HERE)
    time_str = data.get("Time_Start")  # 13:00
    time_obj = datetime.strptime(time_str, "%H:%M")
    formatted_time = time_obj.strftime("%I:%M %p")  # 01:00 PM

    try:
        new_sched = ScheduleMaster(
            Date=formatted_date,
            Time_Start=formatted_time,
            Case_Type=data.get("Case_Type"),
            Case_Number=data.get("Case_Number"),
            Title=data.get("Title"),
            Status="PENDING"
        )

        db.session.add(new_sched)
        db.session.commit()

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

        db.session.commit()

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


