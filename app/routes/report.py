
from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash, url_for, current_app, send_file
from flask_login import login_required
from sqlalchemy import cast, Integer, func
from sqlalchemy.orm import joinedload
from app import db
from app.routes.decorators import require_module
from datetime import datetime, timedelta
import os, json, requests, shutil
from xlrd import open_workbook
from xlutils.copy import copy
from openpyxl import load_workbook
from sqlalchemy import func, or_, and_
from collections import OrderedDict
from app.models import CTMS1000, CTMS4100





reports_bp = Blueprint('reports', __name__, url_prefix='/report')


@reports_bp.route('/')
@login_required
@require_module(16)
def index():

    storage_path = os.path.join(
        current_app.root_path,
        'static',
        'storage'
    )

    os.makedirs(storage_path, exist_ok=True)

    files = []

    for filename in os.listdir(storage_path):

        full_path = os.path.join(storage_path, filename)

        if os.path.isfile(full_path):

            files.append({
                "name": filename,
                "size": round(os.path.getsize(full_path) / 1024, 2),
                "date": datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%Y-%m-%d %I:%M %p")
            })

    # newest first
    files.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "reports/index.html",
        files=files
    )




@reports_bp.route('/delete/<filename>')
@login_required
@require_module(16)
def delete_file(filename):

    storage_path = os.path.join(
        current_app.root_path,
        'static',
        'storage'
    )

    file_path = os.path.join(storage_path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} deleted successfully.", "success")
    else:
        flash("File not found.", "danger")

    return redirect(url_for('reports.index'))


@reports_bp.route('/mrc')
@login_required
@require_module(16)
def mrc():

    # =========================
    # PATHS
    # =========================
    base_file = os.path.join(
        current_app.root_path,
        "static",
        "base_docs",
        "MTC BUENAVISTA, AGUSAN DEL NORTE.xlsx"
    )

    storage_dir = os.path.join(
        current_app.root_path,
        "static",
        "storage"
    )

    os.makedirs(storage_dir, exist_ok=True)

    # =========================
    # DATE FORMAT
    # =========================
    month_param = request.args.get("month")

    if month_param:
        now = datetime.strptime(month_param, "%Y-%m")
    else:
        now = datetime.now()

    month_year_text = now.strftime("%B %Y")

    # ✅ ADD THIS
    month_start = datetime(now.year, now.month, 1)

    # =========================
    # FILE NAME
    # =========================
    base_filename = f"{month_year_text} MTC BUENAVISTA, AGUSAN DEL NORTE.xlsx"

    name, ext = os.path.splitext(base_filename)

    counter = 1
    filename = base_filename

    while os.path.exists(os.path.join(storage_dir, filename)):
        filename = f"{name} ({counter}){ext}"
        counter += 1

    output_path = os.path.join(storage_dir, filename)

    shutil.copy2(base_file, output_path)

    # =========================
    # II-A FILED
    # =========================
    nature_map = {
        "00027": "violation_of_bp_22",
        "00028": "illegal_possession_firearms_ammunition",
        "00029": "estafa_swindling_other_deceits",
        "00030": "adultery_concubinage",
        "00031": "physical_injuries",
        "00032": "acts_of_lasciviousness",
        "00033": "violation_traffic_laws_rules_regulations",
        "00034": "violation_municipal_city_ordinances",
        "00035": "criminal_negligence_reckless_imprudence",
        "00036": "all_other_criminal_cases"
    }

    results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .filter(
            CTMS1000.DTFILED.like(f"{now.strftime('%Y-%m')}%")
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    counts = {code: count for code, count in results}

    # =========================
    # II-B REVIVED
    # =========================
    revived_results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DTREVIVED.like(f"{now.strftime('%Y-%m')}%")
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    revived_counts = {code: count for code, count in revived_results}

    # =========================
    # III-A (ROW 20) NUMBER OF CASES DECIDED/RESOLVED ON THE MERITS
    # =========================
    row20_results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DTRELEASED.like(f"{now.strftime('%Y-%m')}%"),
            CTMS4100.RELEASED.in_(["20002", "20003", "20004","20005","20006","20007","20008","20009"])
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    row20_counts = {code: count for code, count in row20_results}

    # =========================
    # III-B (ROW 21) NUMBER OF CASES DECIDED/RESOLVED BY WAY OF COMPROMISE, JDR, ETC.
    # =========================
    row21_results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DTRELEASED.like(f"{now.strftime('%Y-%m')}%"),
            CTMS4100.RELEASED.in_(["20001"])
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    row21_counts = {code: count for code, count in row21_results}



    row22_results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DTARCHIVED.like(f"{now.strftime('%Y-%m')}%")
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    row22_counts = {code: count for code, count in row22_results}



    row23_results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DTREFERRED.like(f"{now.strftime('%Y-%m')}%")
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    row23_counts = {code: count for code, count in row23_results}


    row14_results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            or_(
                CTMS4100.DECIDECODE != "90002",
                CTMS4100.DECIDECODE == None,
                CTMS4100.DECIDECODE == ""
            )
        )
        .filter(
            or_(
                CTMS4100.DTARRAIGN >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTIARRAIGN >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTPRETRIAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTLTTRIAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTACTUAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTDEMURRER >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTDEFENSE >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTOFFERPRO >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTOFFERDEF >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTREBUTTAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTSURREBUT >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTSUBMIT >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTPROMUL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DPOSTPONED >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTSENTENCE >= month_start.strftime("%Y-%m-%d")
            )
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    row14_counts = {code: count for code, count in row14_results}

    debug_cases = (
        db.session.query(
            CTMS1000.CASENUM,
            CTMS1000.NATURECODE,
            CTMS4100.DTARRAIGN,
            CTMS4100.DTIARRAIGN,
            CTMS4100.DTPRETRIAL,
            CTMS4100.DTLTTRIAL,
            CTMS4100.DTACTUAL,
            CTMS4100.DTDEMURRER,
            CTMS4100.DTDEFENSE,
            CTMS4100.DTOFFERPRO,
            CTMS4100.DTOFFERDEF,
            CTMS4100.DTREBUTTAL,
            CTMS4100.DTSURREBUT,
            CTMS4100.DTSUBMIT,
            CTMS4100.DTPROMUL,
            CTMS4100.DPOSTPONED,
            CTMS4100.DTSENTENCE,
            CTMS4100.DECIDECODE
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            or_(
                CTMS4100.DECIDECODE != "90002",
                CTMS4100.DECIDECODE == None,
                CTMS4100.DECIDECODE == ""
            )
        )
        .filter(
            or_(
                CTMS4100.DTARRAIGN >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTIARRAIGN >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTPRETRIAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTLTTRIAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTACTUAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTDEMURRER >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTDEFENSE >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTOFFERPRO >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTOFFERDEF >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTREBUTTAL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTSURREBUT >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTSUBMIT >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTPROMUL >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DPOSTPONED >= month_start.strftime("%Y-%m-%d"),
                CTMS4100.DTSENTENCE >= month_start.strftime("%Y-%m-%d")
            )
        )
        .all()
    )

    for row in debug_cases:
        print(row)



    # =========================
    # OPEN EXCEL
    # =========================
    wb = load_workbook(output_path)
    ws = wb["Page 1"]

    ws["D12"] = month_year_text

    # =========================
    # II-A WRITE (ROW 16)
    # =========================
    cell_map = {
        "00032": "J16",
        "00030": "H16",
        "00036": "N16",
        "00035": "M16",
        "00029": "G16",
        "00028": "F16",
        "00031": "I16",
        "00027": "E16",
        "00034": "L16",
        "00033": "K16"
    }

    for code, cell in cell_map.items():
        ws[cell] = counts.get(code, 0)

    # =========================
    # II-B WRITE (ROW 17)
    # =========================
    revived_cell_map = {
        "00032": "J17",
        "00030": "H17",
        "00036": "N17",
        "00035": "M17",
        "00029": "G17",
        "00028": "F17",
        "00031": "I17",
        "00027": "E17",
        "00034": "L17",
        "00033": "K17"
    }

    for code, cell in revived_cell_map.items():
        ws[cell] = revived_counts.get(code, 0)

    # =========================
    # III-A WRITE (ROW 20) ✔ FIXED
    # =========================
    row20_cell_map = {
        "00032": "J20",
        "00030": "H20",
        "00036": "N20",
        "00035": "M20",
        "00029": "G20",
        "00028": "F20",
        "00031": "I20",
        "00027": "E20",
        "00034": "L20",
        "00033": "K20"
    }

    for code, cell in row20_cell_map.items():
        ws[cell] = row20_counts.get(code, 0)

    # =========================
    # III-B WRITE (ROW 21) ✔ FIXED
    # =========================
    row21_cell_map = {
        "00032": "J21",
        "00030": "H21",
        "00036": "N21",
        "00035": "M21",
        "00029": "G21",
        "00028": "F21",
        "00031": "I21",
        "00027": "E21",
        "00034": "L21",
        "00033": "K21"
    }

    for code, cell in row21_cell_map.items():
        ws[cell] = row21_counts.get(code, 0)



    row22_cell_map = {
        "00032": "J22",
        "00030": "H22",
        "00036": "N22",
        "00035": "M22",
        "00029": "G22",
        "00028": "F22",
        "00031": "I22",
        "00027": "E22",
        "00034": "L22",
        "00033": "K22"
    }

    for code, cell in row22_cell_map.items():
        ws[cell] = row22_counts.get(code, 0)


    row23_cell_map = {
        "00032": "J23",
        "00030": "H23",
        "00036": "N23",
        "00035": "M23",
        "00029": "G23",
        "00028": "F23",
        "00031": "I23",
        "00027": "E23",
        "00034": "L23",
        "00033": "K23"
    }

    for code, cell in row23_cell_map.items():
        ws[cell] = row23_counts.get(code, 0)

    row14_cell_map = {
        "00032": "J14",
        "00030": "H14",
        "00036": "N14",
        "00035": "M14",
        "00029": "G14",
        "00028": "F14",
        "00031": "I14",
        "00027": "E14",
        "00034": "L14",
        "00033": "K14"
    }

    for code, cell in row14_cell_map.items():
        ws[cell] = row14_counts.get(code, 0)
    # =========================
    # SAVE FILE
    # =========================
    wb.save(output_path)

    flash(f"Report generated: {filename}", "success")
    return redirect(url_for('reports.index'))









@reports_bp.route('/mrc-countingpart1')
@login_required
@require_module(16)
def mrc_countingpart1():

    nature_map = {
        "00027": "violation_of_bp_22",
        "00028": "illegal_possession_firearms_ammunition",
        "00029": "estafa_swindling_other_deceits",
        "00030": "adultery_concubinage",
        "00031": "physical_injuries",
        "00032": "acts_of_lasciviousness",
        "00033": "violation_traffic_laws_rules_regulations",
        "00034": "violation_municipal_city_ordinances",
        "00035": "criminal_negligence_reckless_imprudence",
        "00036": "all_other_criminal_cases"
    }

    results = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    counts = {code: count for code, count in results}

    output = {}

    for code, key in nature_map.items():
        output[key] = counts.get(code, 0)

    return jsonify(output)