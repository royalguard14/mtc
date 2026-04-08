from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User
from werkzeug.security import check_password_hash
from app.routes.helpers import get_all_settings

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    settings = get_all_settings()

    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))

    if request.method == 'POST':

        username_or_email = request.form['username']
        password = request.form['password']

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('core.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('auth.login'))

    return render_template('login.html', settings=settings)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
