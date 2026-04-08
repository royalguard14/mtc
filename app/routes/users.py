from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import User, Role
from app import db
from app.routes.decorators import require_module
from werkzeug.security import generate_password_hash
from app.routes.helpers import get_all_settings

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@login_required
@require_module(2)
def users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template('users/index.html', users=users, roles=roles)

@users_bp.route('/create', methods=['POST'])
@login_required
@require_module(2)
def users_create():
    settings = get_all_settings()
    prefix = settings.get('Email', '')  # 🛡️ Fallback if setting is missing

    # Build full email safely
    user_email = request.form['email'].strip()
    full_email = f"{user_email}@{prefix}" if prefix else user_email

    # Check if user/email already exists (optional but recommended)
    if User.query.filter_by(username=request.form['username']).first():
        flash('Username already exists.', 'warning')
        return redirect(url_for('users.users'))

    if User.query.filter_by(email=full_email).first():
        flash('Email already exists.', 'warning')
        return redirect(url_for('users.users'))

    # Create and save new user
    user = User(
        username=request.form['username'],
        email=full_email,
        role_id=request.form.get('role_id'),
        password=generate_password_hash(request.form['password'])
    )

    db.session.add(user)
    db.session.commit()
    flash('User created successfully.', 'success')
    return redirect(url_for('users.users'))


@users_bp.route('/edit/<int:user_id>', methods=['POST'])
@login_required
@require_module(2)
def users_edit(user_id):
    user = User.query.get_or_404(user_id)
    if user.username.lower() == 'zear':
        if request.form.get('access_password') != 'access':
            flash("Access denied: Cannot edit 'zear' without valid password.", 'error')
            return redirect(url_for('users.users'))

    user.username = request.form['username']
    user.email = request.form['email']
    user.role_id = request.form.get('role_id')
    db.session.commit()
    flash('User updated successfully.', 'success')
    return redirect(url_for('users.users'))

@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
@require_module(2)
def users_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.username.lower() == 'zear':
        flash("Cannot delete protected user 'zear'.", 'error')
        return redirect(url_for('users.users'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('users.users'))
