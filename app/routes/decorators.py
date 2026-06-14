from functools import wraps
from flask import redirect, url_for, request, jsonify
from flask_login import current_user

from app.models import User


def require_module(module_id):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if not current_user.role or module_id not in current_user.role.modules:
                return redirect(url_for('core.unauthorized'))

            return f(*args, **kwargs)

        return wrapped
    return decorator


def remmberToken(f):
    @wraps(f)
    def wrapped(*args, **kwargs):

        token = request.headers.get("Authorization")

        if not token:
            return jsonify({
                "success": False,
                "message": "Token required"
            }), 401

        user = User.query.filter_by(
            remember_token=token,
            isDeleted=False,
            isActive=True
        ).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid token"
            }), 401

        # Optional: make the user available to the route
        request.mobile_user = user

        return f(*args, **kwargs)

    return wrapped