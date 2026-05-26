from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash, current_app, url_for
from flask_login import login_required

from sqlalchemy import cast, Integer, func
from sqlalchemy.orm import joinedload

from app import db
from app.routes.decorators import require_module

from datetime import datetime, timedelta

import os, json, requests

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