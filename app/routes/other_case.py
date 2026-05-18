from flask import Blueprint, render_template, jsonify, request, redirect, flash, url_for
from flask_login import login_required
from app import db
from datetime import datetime
import requests
from sqlalchemy import cast, Integer, func
from app.models import Cases
from app.routes.decorators import require_module
cases_bp = Blueprint('cases', __name__, url_prefix='/cases')
# =========================
# GOOGLE SHEET WEBHOOK
# =========================
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw2My5Z1KySGX-7WwFb9i-JMh7l6e7oDX-xdmbHzrEgOGpEQ1kSALIgal6zmP5kLFBW/exec"
# =========================
# CIVIL CASE LIST
# =========================

@cases_bp.route('/oca')
@login_required
@require_module(6)
def civil_cases():
    CourtRecordsCivil = (
        Cases.query
        .filter(func.lower(Cases.case_type) == "civil case")
        .order_by(Cases.case_number.desc())
        .all()
    )
    return render_template(
        "cases/civil_cases/index.html",
        CourtRecordsCivil=CourtRecordsCivil
    )
# =========================
# SMALL CLAIMS LIST
# =========================

@cases_bp.route('/scc')
@login_required
@require_module(7)
def small_claims():
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
    return render_template(
        "cases/small_claims/index.html",
        CourtRecordsSclaims=CourtRecordsSclaims
    )

@cases_bp.route('/create', methods=['POST'])
@login_required
def create_case():
    data = request.get_json() or {}
    case_number = data.get('case_number')
    title = data.get('title')
    nature = data.get('nature') or ""
    case_type = data.get('case_type')
    date_str = data.get('date_filed')
    # =========================
    # VALIDATION FIRST (IMPORTANT ORDER)
    # =========================
    if not case_number or not title:
        return jsonify({
            "status": "error",
            "message": "Case number and Title required"
        }), 400
    # =========================
    # DUPLICATE CHECK
    # =========================
    existing = Cases.query.filter_by(case_number=case_number).first()
    if existing:
        return jsonify({
            "status": "error",
            "message": "Case number already exists"
        }), 400
    # =========================
    # SAFE DATE PARSE
    # =========================
    date_filed = None
    if date_str:
        try:
            date_filed = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            date_filed = None
    # =========================
    # CREATE CASE
    # =========================
    new_case = Cases(
        case_number=case_number,
        title=title,
        nature=nature,
        date_filed=date_filed,
        case_type=case_type.upper()
    )
    db.session.add(new_case)
    db.session.commit()
    # =========================
    # SYNC TO GOOGLE SHEETS
    # =========================
    try:
        sync_to_google_sheet(new_case)
    except Exception as e:
        print("GS SYNC ERROR:", str(e))
    return jsonify({
        "status": "success",
        "message": "Created successfully"
    })
# =========================
# UPDATE CASE
# =========================

@cases_bp.route('/update', methods=['POST'])
@login_required
def update_case():
    data = request.get_json()
    case = Cases.query.get(data['id'])
    if not case:
        return jsonify({
            "status": "error",
            "message": "Not found"
        }), 404
    try:
        case.case_number = data.get('case_number')
        case.title = data.get('title')
        case.nature = data.get('nature') or ""
        date_str = data.get('date_filed')
        if date_str:
            try:
                case.date_filed = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                case.date_filed = None
        db.session.commit()
        sync_to_google_sheet(case)
        flash('Case updated successfully.', 'success')
        return jsonify({
            "status": "success",
            "message": "Updated successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
# =========================
# GOOGLE SHEET UPSERT (IMPORTANT CORE)
# =========================
def sync_to_google_sheet(case):
    payload = {
        "type": "UPSERT",
        "sheet": "other_cases",   # ✅ ONE SHEET ONLY
        "keyColumn": "case_number",
        "keyValue": case.case_number,
        "data": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "nature": case.nature or "",
            "date_filed": str(case.date_filed) if case.date_filed else "",
            "case_type": case.case_type
        }
    }
    try:
        requests.post(GOOGLE_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print("Google Sync Error:", str(e))
# =========================
# FULL SYNC (MANUAL BUTTON / BACKUP)
# =========================

@cases_bp.route('/api/sync-other-cases')
@login_required
def sync_other_cases():
    cases = Cases.query.order_by(Cases.id.asc()).all()
    headers = [
        "id",
        "case_number",
        "title",
        "nature",
        "date_filed",
        "case_type"
    ]
    data = []
    for c in cases:
        data.append([
            c.id,
            c.case_number,
            c.title,
            c.nature,
            str(c.date_filed) if c.date_filed else "",
            c.case_type
        ])
    payload = {
        "type": "FULL_SYNC",
        "sheet": "other_cases",
        "headers": headers,
        "data": data
    }
    try:
        response = requests.post(
            GOOGLE_WEBHOOK_URL,
            json=payload,
            timeout=60
        )
        return jsonify({
            "status": "success",
            "google_response": response.text,
            "total": len(data)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500