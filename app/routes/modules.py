from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import Module, Role
from app import db
from app.routes.decorators import require_module
from sqlalchemy.orm.attributes import flag_modified
from app.utils import extract_fa_icons
import os

modules_bp = Blueprint('modules', __name__, url_prefix='/modules')


@modules_bp.route('/')
@login_required
@require_module(3)
def modules():
    css_path = os.path.join(current_app.static_folder, 'plugins/fontawesome-free/css/all.min.css')
    icons = extract_fa_icons(css_path)
    modules = Module.query.all()
    return render_template('modules/index.html', modules=modules, icons=icons)


@modules_bp.route('/create', methods=['POST'])
@login_required
@require_module(3)
def modules_create():
    icon = request.form['icon'].replace('fas ', '').replace('far ', '').replace('fab ', '')  # Normalize
    module = Module(
        name=request.form['name'],
        icon=icon,
        url=request.form['url'],
        description=request.form.get('description')
    )
    db.session.add(module)
    db.session.commit()
    flash('Module created successfully.', 'success')
    return redirect(url_for('modules.modules'))


@modules_bp.route('/edit/<int:module_id>', methods=['POST'])
@login_required
@require_module(3)
def modules_edit(module_id):
    module = Module.query.get_or_404(module_id)
    module.name = request.form['name']
    module.icon = request.form['icon'].replace('fas ', '').replace('far ', '').replace('fab ', '')  # Normalize
    module.url = request.form['url']
    module.description = request.form.get('description')
    db.session.commit()
    flash('Module updated successfully.', 'success')
    return redirect(url_for('modules.modules'))


@modules_bp.route('/delete/<int:module_id>', methods=['POST'])
@login_required
@require_module(3)
def modules_delete(module_id):
    # 🔒 Prevent deletion of protected modules (ID 1–4)
    if module_id in range(1, 5):
        flash('Cannot delete protected module.', 'error')
        return redirect(url_for('modules.modules'))

    # ✅ Continue only if not protected
    module = Module.query.get_or_404(module_id)

    # Remove this module from all role assignments
    roles = Role.query.all()
    for role in roles:
        if role.modules and module_id in role.modules:
            role.modules.remove(module_id)
            flag_modified(role, "modules")

    db.session.delete(module)
    db.session.commit()
    flash('Module deleted and removed from all role assignments.', 'success')
    return redirect(url_for('modules.modules'))
