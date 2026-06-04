
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
from app.models import CTMS1000, CTMS4100, Cases
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from openpyxl.utils import get_column_letter
from sqlalchemy import cast, String
from collections import Counter




reports_bp = Blueprint('reports', __name__, url_prefix='/report')



civil_list = {
    "10001": "Small Claims",
    "10002": "Ejectment",
    "10003": "Other Cases under Summary Procedure",
    "10004": "Cases under Regular Procedure",
    "10005": "Election",
    "10006": "Other Civil Cases"
}


def classify_civil_case(title):
    if not title:
        return "10006"  # Other Civil Cases

    text = title.upper().strip()

    # Ejectment
    if any(x in text for x in [
        "UNLAWFUL DETAINER",
        "FORCIBLE ENTRY"
    ]):
        return "10002"

    # Election
    if any(x in text for x in [
        "ELECTION",
        "ELECTION PROTEST",
        "QUO WARRANTO"
    ]):
        return "10005"

    # Small Claims
    if "SMALL CLAIM" in text:
        return "10001"

    # Other Summary Procedure
    if "SUMMARY PROCEDURE" in text:
        return "10003"

    # Default
    return "10004"  # Cases under Regular Procedure

def get_civil_case_counts(query):
    """
    query must return Cases.nature
    """

    counter = Counter()

    for (nature,) in query.all():
        code = classify_civil_case(nature)
        counter[code] += 1

    return [
        (code, counter.get(code, 0))
        for code in civil_list.keys()
    ]


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

 
    month_start = datetime(now.year, now.month, 1)
   

    next_month_start = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)


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
    # ROW CONFIG
    # =========================
    rows = [14, 16, 17, 18, 20, 21, 22, 23]

    nature_list = ["00027","00028","00029","00030","00031","00032","00033","00034","00035","00036"]
    civil_list = ["10001","10002","10003","10004","10005","10006"]
    start_col = 5  

    # =========================
    # PAGE 1 Counting Result
    # =========================

    p1_row16_result = (
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

    p1_row17_result = (
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

    p1_row20_result = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DECIDECODE == "90002",
            CTMS4100.DTPROMUL.like(f"{now.strftime('%Y-%m')}%"),
            CTMS4100.DECIDETYPE == "ON_MERITS"
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )

    p1_row21_result = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DECIDECODE != "90002",
            CTMS4100.DTPROMUL.like(f"{now.strftime('%Y-%m')}%"),
            CTMS4100.DECIDETYPE != "ON_MERITS"
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )



    p1_row22_result = (
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

    p1_row23_result = (
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

    p1_row14_result = (
        db.session.query(
            CTMS1000.NATURECODE,
            func.count(CTMS1000.NATURECODE)
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            and_(
                CTMS4100.OTHER_STATUS.isnot(None),
                CTMS4100.OTHER_STATUS != '',
                func.instr(CTMS4100.OTHER_STATUS, '|') > 0,

                func.substr(
                    CTMS4100.OTHER_STATUS,
                    func.instr(CTMS4100.OTHER_STATUS, '|') + 1
                ) >= month_start.strftime("%Y-%m-%d"),

                func.substr(
                    CTMS4100.OTHER_STATUS,
                    func.instr(CTMS4100.OTHER_STATUS, '|') + 1
                ) < next_month_start.strftime("%Y-%m-%d")
            )
        )
        .group_by(CTMS1000.NATURECODE)
        .all()
    )


    # =========================
    # PAGE 2 Counting Result
    # =========================

    query = (
        db.session.query(Cases.nature)
        .filter(
            Cases.date_filed.like(f"{now.strftime('%Y-%m')}%")
        )
    )

    p2_row16_result = get_civil_case_counts(query)

    query = (
        db.session.query(Cases.nature)
        .filter(
            func.json_extract(Cases.action, '$.revived_date').like(f"{now.strftime('%Y-%m')}%"),
        )
    )
    p2_row17_result = get_civil_case_counts(query)



    query = (
        db.session.query(Cases.nature)
        .filter(
            func.json_extract(Cases.action, '$.decision_date').like(f"{now.strftime('%Y-%m')}%"),

            func.json_extract(Cases.action, '$.decision_type') == "ON_MERIT",

        )
    )
    p2_row20_result = get_civil_case_counts(query)

    query = (
        db.session.query(Cases.nature)
        .filter(
            func.json_extract(Cases.action, '$.decision_date').like(f"{now.strftime('%Y-%m')}%"),

            func.json_extract(Cases.action, '$.decision_type') != "ON_MERIT",

        )
    )
    p2_row21_result = get_civil_case_counts(query)

    query = (
        db.session.query(Cases.nature)
        .filter(
            func.json_extract(Cases.action, '$.archived_date').like(f"{now.strftime('%Y-%m')}%"),

        )
    )
    p2_row22_result = get_civil_case_counts(query)
 

    query = (
        db.session.query(Cases.nature)
        .filter(
            func.json_extract(Cases.action, '$.referred_date').like(f"{now.strftime('%Y-%m')}%"),

        )
    )
    p2_row23_result = get_civil_case_counts(query)

    # =========================
    # COUNT DICTS
    # =========================

    p1_counts = {
        14: dict(p1_row14_result),
        16: dict(p1_row16_result),
        17: dict(p1_row17_result),
        18: {},
        20: dict(p1_row20_result),
        21: dict(p1_row21_result),
        22: dict(p1_row22_result),
        23: dict(p1_row23_result),
    }


    p2_counts = {
        # 14: dict(p1_row14_result),
        16: dict(p2_row16_result),
        17: dict(p2_row17_result),
        18: {},
        20: dict(p2_row20_result),
        21: dict(p2_row21_result),
        22: dict(p2_row22_result),
        23: dict(p2_row23_result)
    }

    april_2026_override = {
        "00027": 0,
        "00028": 0,
        "00029": 12,
        "00030": 0,
        "00031": 0,
        "00032": 1,
        "00033": 0,
        "00034": 0,
        "00035": 0,
        "00036": 4
    }




    # =========================
    # EXCEL MAP BUILDER
    # =========================

    p1_maps = {
        row: {
            code: f"{get_column_letter(start_col + i)}{row}"
            for i, code in enumerate(nature_list)
        }
        for row in rows
    }


    p2_maps = {
        row: {
                code: f"{get_column_letter(start_col + i)}{row}"
                for i, code in enumerate(civil_list)
        }
            for row in rows
    }



    # =========================
    # OPEN EXCEL
    # =========================
    wb = load_workbook(output_path)
    ws = wb["Page 1"]
    ws2 = wb["Page 2"]
    ws["D12"] = month_year_text

    # =========================
    # Page 1 here
    # =========================    

    for row in rows:
        for code, cell in p1_maps[row].items():

            value = p1_counts.get(row, {}).get(code, 0)

            # =========================
            # SPECIAL CASE FIX (example)
            # =========================
            if row == 17 and month_start.year == 2026 and month_start.month == 4:
                if code == "00031":
                    value -= 1
            # =========================
        # SPECIAL CASE: ROW 14 (APRIL 2026 OVERRIDE)
        # =========================
            if row == 14 and month_start.year == 2026 and month_start.month == 4:
                value = april_2026_override.get(code, 0)

            ws[cell] = value

    # =========================
    # Page 2 here
    # =========================
    
    for row in rows:
        for code, cell in p2_maps[row].items():

            value = p2_counts.get(row, {}).get(code, 0)

            ws2[cell] = value



    # =========================
    # SAVE FILE
    # =========================
    wb.save(output_path)

    flash(f"Report generated: {filename}", "success")
    return redirect(url_for('reports.index'))


@reports_bp.route('/mrc/table')
@login_required
@require_module(16)
def mrc_table():

    # =========================
    # DATE
    # =========================
    month_param = request.args.get("month")

    if month_param:
        now = datetime.strptime(month_param, "%Y-%m")
    else:
        now = datetime.now()

    month_start = datetime(now.year, now.month, 1)
    next_month_start = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

    month_label = now.strftime("%B %Y")

    # =========================
    # NEWLY FILED CASES
    # =========================
    filed_cases = (
        db.session.query(
            CTMS1000.CASEID,
            CTMS1000.CASENUM,
            CTMS1000.CASETITLE,
            CTMS1000.NATURECODE,
            CTMS1000.DTFILED,
            CTMS1000.NATUREREM,
        )
        .filter(
            CTMS1000.DTFILED.like(f"{now.strftime('%Y-%m')}%")
        )
        .all()
    )

    # =========================
    # DISPOSED CASES
    # =========================
    disposed_cases = (
        db.session.query(
            CTMS1000.CASEID,
            CTMS1000.CASENUM,
            CTMS1000.CASETITLE,
            CTMS1000.NATURECODE,
            CTMS4100.DTRELEASED,
            CTMS4100.DECIDETYPE,
            CTMS1000.NATUREREM
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            CTMS4100.DTRELEASED.like(f"{now.strftime('%Y-%m')}%"),
            CTMS4100.DECIDETYPE.isnot(None)
        )
        .all()
    )

  # =========================
    # PENDING CASES (same basis as Row 14)
    # =========================
    pending_cases = (
        db.session.query(
            CTMS1000.CASEID,
            CTMS1000.CASENUM,
            CTMS1000.CASETITLE,
            CTMS1000.NATURECODE,
            CTMS1000.NATUREREM,
            CTMS1000.DTFILED,
            CTMS4100.OTHER_STATUS
        )
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            and_(
                CTMS4100.OTHER_STATUS.isnot(None),
                CTMS4100.OTHER_STATUS != '',
                func.instr(CTMS4100.OTHER_STATUS, '|') > 0,

                func.substr(
                    CTMS4100.OTHER_STATUS,
                    func.instr(CTMS4100.OTHER_STATUS, '|') + 1
                ) >= month_start.strftime("%Y-%m-%d"),

                func.substr(
                    CTMS4100.OTHER_STATUS,
                    func.instr(CTMS4100.OTHER_STATUS, '|') + 1
                ) < next_month_start.strftime("%Y-%m-%d")
            )
        )
        .order_by(CTMS1000.CASENUM)
        .all()
    )

    return render_template(
        "reports/mrc_table.html",
        month_label=month_label,
        filed_cases=filed_cases,
        disposed_cases=disposed_cases,
        pending_cases=pending_cases
    )