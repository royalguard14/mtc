from flask import Blueprint, render_template, session, request, jsonify
from app.routes.helpers import get_all_settings
from flask_login import login_required
from app.routes.decorators import require_module
from datetime import datetime

from sqlalchemy import or_ , extract
from app.models import (
    ScheduleMaster,
    Cases,
    CTMS1000,
    CTMS4000,
    CivilWedding,
    Certificate
)

import requests

core_bp = Blueprint('core', __name__)

@core_bp.route("/")
def index():
    settings = get_all_settings()
    landing = settings.get('Landing')

    if landing == '0':
        return render_template("login.html", settings=settings)
    return render_template("home.html", settings=settings)


@core_bp.route('/dashboard')
@login_required
def dashboard():

    # =========================================
    # TOTAL COUNTS
    # =========================================
    criminalCounts = CTMS1000.query.count()

    civilCounts = Cases.query.filter(
        Cases.case_type.ilike("CIVIL CASE")
    ).count()

    smallclaimsCounts = Cases.query.filter(
        Cases.case_type.ilike("SMALLCLAIMS")
    ).count()

    # =========================================
    # THIS MONTH COUNTS
    # =========================================
    current_month = datetime.now().month
    current_year = datetime.now().year

    criminalCaseThisMonth = CTMS1000.query.filter(
        extract('month', CTMS1000.DTRECEIVED) == current_month,
        extract('year', CTMS1000.DTRECEIVED) == current_year
    ).count()

    civilCasesThisMonth = Cases.query.filter(
        extract('month', Cases.date_filed) == current_month,
        extract('year', Cases.date_filed) == current_year
    ).count()

    totalCaseThisMonth = criminalCaseThisMonth + civilCasesThisMonth

    # =========================================
    # SCHEDULES FOR CALENDAR (🔥 NEW ADDITION)
    # =========================================
    schedules = ScheduleMaster.query.all()


    events_map = {}

    for s in schedules:
        data = s.to_dict()

        print("RAW DATA:", data)  # 🔥 DEBUG

        if not data.get("Date") or not data.get("Time Start"):
            continue

        try:
            raw = f"{data['Date']} {data['Time Start']}"
            dt = datetime.strptime(raw, "%m/%d/%Y %I:%M %p")
        except Exception as e:
            print("DATE PARSE ERROR:", raw, e)
            continue

        case_type = (data.get("Case Type") or "").upper()
        case_no = data.get("Case Number") or data.get("Title")

        if not (case_type or case_no):
            continue

        key = f"{case_type}-{case_no}-{dt.strftime('%Y-%m-%dT%H:%M:%S')}"

        if key in events_map:
            continue

        events_map[key] = {
            "title": (
                data["Title"] if case_type == "WEDDING"
                else f"{data.get('Case Type')} - {case_no}"
            ),
            "start": dt.strftime("%Y-%m-%dT%H:%M:%S")
        }

    events = list(events_map.values())

    print("FINAL EVENTS:", events)  # 🔥 DEBUG

    # =========================================
    # DASHBOARD DATA
    # =========================================
    dashboard_data = {
        "criminalCounts": criminalCounts,
        "civilCounts": civilCounts,
        "smallclaimsCounts": smallclaimsCounts,
        "criminalCaseThisMonth": criminalCaseThisMonth,
        "civilCasesThisMonth": civilCasesThisMonth,
        "totalCaseThisMonth": totalCaseThisMonth,
        "events": events
    }

    return render_template(
        "dashboard.html",
        dashboard_data=dashboard_data
    )
@core_bp.route("/dashboard/v1")
@require_module(1)
def dashboard_v1():
    return render_template("error.html")

@core_bp.app_errorhandler(500)
def server_error(error):
    return render_template('error.html', error_message='Server error (500).')

@core_bp.route('/unauthorized')
def unauthorized():
    return render_template('error.html', error_message="Unauthorized Access"), 403




# =========================================
# GLOBAL SEARCH API
# =========================================
@core_bp.route("/search/api")
@login_required
def global_search_api():

    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    results = []

    # =====================================
    # CRIMINAL CASES
    # =====================================

    criminal_cases = (
        CTMS1000.query.filter(
            or_(
                CTMS1000.CASENUM.ilike(f"%{q}%"),
                CTMS1000.CASETITLE.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    for item in criminal_cases:

        results.append({
            "label": f"Criminal Case: {item.CASENUM} | {item.CASETITLE}"
        })

    # =====================================
    # PERSONS
    # =====================================

    persons = (
        CTMS4000.query.filter(
            or_(
                CTMS4000.FNAME.ilike(f"%{q}%"),
                CTMS4000.LNAME.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    for item in persons:

        fullname = f"{item.FNAME or ''} {item.LNAME or ''}"

        results.append({
            "label": "Accused: " + fullname.strip()
        })

    # =====================================
    # CIVIL CASES
    # =====================================

    civil_cases = (
        Cases.query.filter(
            or_(
                Cases.case_number.ilike(f"%{q}%"),
                Cases.title.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    for item in civil_cases:

        case_type = (item.case_type or "").lower()

        if case_type == "civil case":

            results.append({
                "label": f"Civil Case: {item.case_number} | {item.title}"
            })

        elif case_type == "smallclaims" or case_type == "small claims case":

            results.append({
                "label": f"Small Claims: {item.case_number} | {item.title}"
            })

        else:

            results.append({
                "label": f"{item.case_type or 'Case'}: {item.case_number} | {item.title}"
            })
    # =====================================
    # WEDDINGS
    # =====================================

    weddings = (
        CivilWedding.query.filter(
            or_(
                CivilWedding.groom.ilike(f"%{q}%"),
                CivilWedding.bride.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    for item in weddings:

        results.append({
            "label": f"Couple: {item.groom} & {item.bride}"
        })

    # =====================================
    # CERTIFICATES
    # =====================================

    certificates = (
        Certificate.query.filter(
            Certificate.full_name.ilike(f"%{q}%")
        )
        .limit(10)
        .all()
    )

    for item in certificates:

        results.append({
            "label": item.full_name
        })

    return jsonify(results)