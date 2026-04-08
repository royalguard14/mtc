from flask import Blueprint, render_template
from flask_login import login_required

from app.routes.decorators import require_module
from app.routes.helpers import import_all_dbf

criminals_bp = Blueprint('criminals', __name__, url_prefix='/cc')


@criminals_bp.route('/')
@login_required
@require_module(9)
def criminal():
    return "Hello"


# =========================
# IMPORT ROUTE (TEMP / ADMIN USE)
# =========================

@criminals_bp.route('/import-dbfs')
@login_required
def import_dbfs():
    folder = r"C:\CTMS\dbf"

    import_all_dbf(folder)

    return "✅ DBF Import Completed"