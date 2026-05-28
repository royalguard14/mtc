
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

    # =========================
    # BASE FILE NAME
    # =========================
    base_filename = f"{month_year_text} MTC BUENAVISTA, AGUSAN DEL NORTE.xlsx"

    name, ext = os.path.splitext(base_filename)

    counter = 1
    filename = base_filename

    # =========================
    # AUTO VERSIONING (1)(2)(3)
    # =========================
    while os.path.exists(os.path.join(storage_dir, filename)):
        filename = f"{name} ({counter}){ext}"
        counter += 1

    output_path = os.path.join(storage_dir, filename)

    # =========================
    # COPY TEMPLATE FIRST (PRESERVE FORMAT)
    # =========================
    shutil.copy2(base_file, output_path)

    # =========================
    # OPEN EXCEL (.xlsx)
    # =========================
    wb = load_workbook(output_path)
    ws = wb["Page 1"]

    # =========================
    # WRITE VALUE TO D12
    # =========================
    ws["D12"] = month_year_text

    # =========================
    # SAVE FILE
    # =========================
    wb.save(output_path)

    flash(f"Report generated: {filename}", "success")
    return redirect(url_for('reports.index'))