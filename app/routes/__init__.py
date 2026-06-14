from .auth import auth_bp
from .core import core_bp
from .roles import roles_bp
from .users import users_bp
from .modules import modules_bp
from .settings import settings_bp
from .criminal_case import criminals_bp
from .schedule import schedule_bp
from .other_case import cases_bp
from .wedding import wedding_bp
from .generate import generate_bp
from .clearance import clearance_bp
from .dfo import dev_bp
from .report import reports_bp
from .mobile import mobile_bp


blueprints = [
    auth_bp,
    core_bp,
    roles_bp,
    users_bp,
    modules_bp,
    settings_bp,
    criminals_bp,
    schedule_bp,
    cases_bp,
    wedding_bp,
    generate_bp,
    clearance_bp,
    dev_bp,
    reports_bp,
    mobile_bp

]
