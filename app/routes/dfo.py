from flask import Blueprint, flash, url_for, redirect
from flask_login import login_required, current_user, login_user
from app import db
from app.routes.decorators import require_module
from app.models import Certificate, ScheduleMaster
from app.routes.helpers import delete_google_sheet_schedule

dev_bp = Blueprint('developer', __name__, url_prefix='/developer')


@dev_bp.route('/delete-clearance/<int:clearance_id>', methods=['POST'])
@login_required
@require_module(5)
def clearance_delete(clearance_id):

    # extra safety check (role + username)
    if current_user.role.id != 1 or current_user.username != 'zear':
        flash('WARNING!!! FOR CLERK FUNCTION ONLY', 'danger')
        return redirect(url_for('clearance.index'))

    clearance = Certificate.query.get_or_404(clearance_id)

    db.session.delete(clearance)
    db.session.commit()

    flash('Clearance deleted successfully.', 'success')
    return redirect(url_for('clearance.index'))


@dev_bp.route('/delete-sched/<int:id>', methods=['POST'])
@login_required
@require_module(11)
def delete_schedule(id):

    if not (current_user.role.id == 1 and current_user.username == 'zear'):
        flash('WARNING!!! FOR CLERK FUNCTION ONLY', 'danger')
        return redirect(url_for('schedule.wedsched'))

    xxx = ScheduleMaster.query.get_or_404(id)

    case_type = (xxx.Case_Type or "").lower()

    # DELETE
    db.session.delete(xxx)
    db.session.commit()
    delete_google_sheet_schedule(xxx.id)  # optional
    

    flash('Schedule deleted successfully.', 'success')

    if case_type == "wedding":
        return redirect(url_for('schedule.wedsched'))

    return redirect(url_for('schedule.courtsched'))