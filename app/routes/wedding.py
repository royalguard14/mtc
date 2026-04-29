from flask import Blueprint, render_template, jsonify, request, redirect, Response, flash
from flask_login import login_required
from app import db
from datetime import datetime, timedelta
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app.routes.decorators import require_module



wedding_bp = Blueprint('wedding', __name__, url_prefix='/wedding')


@wedding_bp.route('/')
@login_required
@require_module(11)
def index():
	return render_template(
        'wedding/index.html')