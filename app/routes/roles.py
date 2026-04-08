from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Role, Module, User
from app import db
from app.routes.decorators import require_module


roles_bp = Blueprint('roles', __name__, url_prefix='/roles')

@roles_bp.route('/')
@login_required
@require_module(1)
def roles():
    roles = Role.query.all()
    modules = Module.query.all()
    module_lookup = {m.id: m.name for m in modules}
    return render_template('roles/index.html', roles=roles, modules=modules, module_lookup=module_lookup)

@roles_bp.route('/create', methods=['POST'])
@login_required
@require_module(1)
def roles_create():
    role_name = request.form['role_name']
    selected_modules = list(map(int, request.form.getlist('modules')))

    if Role.query.filter_by(role_name=role_name).first():
        flash('Role name already exists.', 'warning')
    else:
        role = Role(role_name=role_name, modules=selected_modules)
        db.session.add(role)
        db.session.commit()
        flash('Role created successfully!', 'success')
    return redirect(url_for('roles.roles'))

@roles_bp.route('/edit/<int:role_id>', methods=['POST'])
@login_required
@require_module(1)
def roles_edit(role_id):
    role = Role.query.get_or_404(role_id)
    role.role_name = request.form['role_name']
    db.session.commit()
    flash('Role name updated successfully.', 'success')
    return redirect(url_for('roles.roles'))

@roles_bp.route('/modules/<int:role_id>', methods=['POST'])
@login_required
@require_module(1)
def roles_update_modules(role_id):
    role = Role.query.get_or_404(role_id)
    selected_modules = list(map(int, request.form.getlist('modules')))
    role.modules = selected_modules
    db.session.commit()
    flash('Modules updated successfully.', 'success')
    return redirect(url_for('roles.roles'))

@roles_bp.route('/delete/<int:role_id>', methods=['POST'])
@login_required
@require_module(1)
def roles_delete(role_id):
    if role_id == 1:
        flash("Cannot delete the default 'Developer' role.", 'error')
        return redirect(url_for('roles.roles'))

    if User.query.filter_by(role_id=role_id).first():
        flash('Cannot delete role. It is assigned to one or more users.', 'error')
        return redirect(url_for('roles.roles'))

    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully.', 'success')
    return redirect(url_for('roles.roles'))
