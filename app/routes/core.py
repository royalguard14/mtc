from flask import Blueprint, render_template, session, request, jsonify
from app.routes.helpers import get_all_settings
from flask_login import login_required
from app.routes.decorators import require_module

from sqlalchemy import or_
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
    return render_template("dashboard.html")

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