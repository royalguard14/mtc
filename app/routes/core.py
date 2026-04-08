from flask import Blueprint, render_template, session
from app.routes.helpers import get_all_settings
from flask_login import login_required
from app.routes.decorators import require_module

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
