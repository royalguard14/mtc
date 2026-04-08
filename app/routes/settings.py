from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Setting
from app import db
from app.routes.decorators import require_module

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
@require_module(4)
def settings():
    settings = Setting.query.order_by(Setting.created_at.desc()).all()
    return render_template('settings/index.html', settings=settings)

@settings_bp.route('/create', methods=['POST'])
@login_required
@require_module(4)
def settings_create():
    setting = Setting(
        function_desc=request.form['function_desc'],
        function=request.form['function'],
        type=request.form['type']
    )
    db.session.add(setting)
    db.session.commit()
    flash('Setting created successfully.', 'success')
    return redirect(url_for('settings.settings'))

@settings_bp.route('/edit/<int:setting_id>', methods=['POST'])
@login_required
@require_module(4)
def settings_edit(setting_id):
    setting = Setting.query.get_or_404(setting_id)

    if setting.function in ['0', '1']:
        setting.function = '1' if request.form.get('function') == '1' else '0'
    else:
        setting.function = request.form['function']

    setting.type = request.form['type']
    db.session.commit()
    flash('Setting updated successfully.', 'success')
    return redirect(url_for('settings.settings'))

@settings_bp.route('/delete/<int:setting_id>', methods=['POST'])
@login_required
@require_module(4)
def settings_delete(setting_id):
    if setting_id in range(1, 9):
        flash('Cannot delete protected setting.', 'error')
        return redirect(url_for('settings.settings'))

    setting = Setting.query.get_or_404(setting_id)
    db.session.delete(setting)
    db.session.commit()
    flash('Setting deleted successfully.', 'success')
    return redirect(url_for('settings.settings'))
