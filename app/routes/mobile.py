from app.models import CTMS1000,CTMS4100, User, Module, Role
from sqlalchemy import or_, and_
from app.routes.decorators import remmberToken
from flask import Blueprint, jsonify, request, url_for
from werkzeug.security import check_password_hash
from secrets import token_urlsafe
from app import db



mobile_bp = Blueprint('apis', __name__, url_prefix='/api')



@mobile_bp.route('/person/allcriminal')

def apiCriminal():

    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    results = []

    # =====================================
    # CRIMINAL CASES
    # =====================================

    criminal_cases = (
        db.session.query(CTMS1000, CTMS4100)
        .join(CTMS4100, CTMS4100.CASEID == CTMS1000.CASEID)
        .filter(
            or_(
                CTMS1000.CASENUM.ilike(f"%{q}%"),
                CTMS1000.CASETITLE.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    for case, party in criminal_cases:

        results.append({
            "type": "case",
            "id": case.CASEID,
            "label": f"Case: {case.CASENUM} | {case.CASETITLE}",
            "url": url_for("criminals.view_person", person_id=party.PERSONID)
        })


    return jsonify(results)


@mobile_bp.route('/login', methods=['POST'])
def mobile_login():

    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        }), 400

    user = User.query.filter_by(
        username=username,
        isDeleted=False,
        isActive=True
    ).first()

    if not user:
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401

    if not check_password_hash(user.password, password):
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401

    # Generate token if missing
    if not user.remember_token:
        user.remember_token = token_urlsafe(64)

    # Get module IDs from role JSON
    module_ids = user.role.modules if user.role else []

    # Load modules from database
    modules = {
        module.id: module
        for module in Module.query.filter(
            Module.id.in_(module_ids)
        ).all()
    }

    # Keep the same order as role.modules
    routes = [
        {
            'id': module_id,
            'name': modules[module_id].name,
            'url': modules[module_id].url
        }
        for module_id in module_ids
        if module_id in modules
    ]

    db.session.commit()

    return jsonify({
        'success': True,
        'token': user.remember_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.role_name if user.role else None
        },
        'routes': routes
    }), 200