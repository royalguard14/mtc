from functools import wraps
from flask import redirect, url_for
from flask_login import current_user


def require_module(module_id):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Ensure user is logged in
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            # Check module access
            if not current_user.role or module_id not in current_user.role.modules:
                return redirect(url_for('core.unauthorized'))

            return f(*args, **kwargs)
        return wrapped
    return decorator
