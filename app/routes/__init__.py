from .auth import auth_bp
from .core import core_bp
from .roles import roles_bp
from .users import users_bp
from .modules import modules_bp
from .settings import settings_bp
from .criminal_case import criminals_bp
from .wedding import wedding_bp

blueprints = [
    auth_bp,
    core_bp,
    roles_bp,
    users_bp,
    modules_bp,
    settings_bp,
    criminals_bp,
    wedding_bp
]
