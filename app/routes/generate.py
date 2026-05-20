from flask import Blueprint, render_template, jsonify, request, redirect, flash, url_for
from flask_login import login_required
from app import db
from datetime import datetime

from app.routes.decorators import require_module

generate_bp = Blueprint('generate', __name__, url_prefix='/generate')


@generate_bp.route('/')
@login_required
def generate_index():


    return render_template(
        "generation/index.html"
    )