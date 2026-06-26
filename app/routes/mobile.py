from app.models import CTMS1000,CTMS4100, User, Module, Role, Cases, NotesStatus
from sqlalchemy import or_, and_, cast, Integer, func
from app.routes.decorators import remmberToken
from flask import Blueprint, jsonify, request, url_for
from werkzeug.security import check_password_hash
from secrets import token_urlsafe
from app import db
from sqlalchemy.orm import joinedload
from datetime import datetime



mobile_bp = Blueprint('apis', __name__, url_prefix='/api')



@mobile_bp.route('/person/allcriminal')
@remmberToken
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



@mobile_bp.route('/cc')
@remmberToken
def getCR():

    try:
        cases = (
            CTMS1000.query
            .order_by(CTMS1000.CASENUM.desc())
            
            .all()
        )

        return jsonify({
            "success": True,
            "message": "Cases retrieved successfully.",
            "data": [
                {
                    "CASEID": case.CASEID,
                    "CASENUM": case.CASENUM,
                    "CASETITLE": case.CASETITLE,
                    "DTFILED": case.DTFILED,
           
                }
                for case in cases
            ]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "data": []
        }), 500


@mobile_bp.route('/cases/oca')
@remmberToken
def getOC():

    try:
        CourtRecordsCivil = (
            Cases.query
            .filter(func.lower(Cases.case_type) == "civil case")
            .order_by(Cases.id.desc())
            .all()
        )

        return jsonify({
            "success": True,
            "message": "Cases retrieved successfully.",
            "data": [
                {
                    "CASEID": case.id,
                    "CASENUM": case.case_number,
                    "CASETITLE": case.title,
                    "DTFILED": case.date_filed.strftime("%Y-%m-%d") if case.date_filed else None,
                }
                for case in CourtRecordsCivil
            ]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "data": []
        }), 500


@mobile_bp.route('/cases/scc')
@remmberToken
def getSC():

    try:
        CourtRecordsCivil = (
            Cases.query
            .filter(func.lower(Cases.case_type) == "smallclaims")
            .order_by(Cases.id.desc())
            .all()
        )

        return jsonify({
            "success": True,
            "message": "Cases retrieved successfully.",
            "data": [
                {
                    "CASEID": case.id,
                    "CASENUM": case.case_number,
                    "CASETITLE": case.title,
                    "DTFILED": case.date_filed.strftime("%Y-%m-%d") if case.date_filed else None,
                }
                for case in CourtRecordsCivil
            ]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "data": []
        }), 500


@mobile_bp.route('/notes')
@remmberToken
def getNotes():
    casedb = request.args.get("casedb", "").strip()
    caseid = request.args.get("caseid", "").strip()

    notes = db.session.query(
        NotesStatus.date,
        NotesStatus.status
    ).filter(
        NotesStatus.case_type == "CRIMINAL",
        NotesStatus.case_id == caseid
    ).order_by(
        NotesStatus.date.desc()
    ).all()

    return jsonify({
        "success": True,
        "notes": [
            {
                "date": note.date.strftime("%m/%d/%Y"),
                "status": note.status
            }
            for note in notes
        ]
    })


@mobile_bp.route('/caseid')
#@remmberToken
def getCASESID():

    caseid = request.args.get("caseid", "").strip()

    records = db.session.query(
        CTMS4100,
        CTMS1000.CASENUM,
        CTMS1000.DTFILED
    ).outerjoin(
        CTMS1000,
        CTMS1000.CASEID == CTMS4100.CASEID
    ).filter(
        CTMS4100.CASEID == caseid
    ).all()

    return jsonify({
        "success": True,
        "records": [
            {
                **record.to_dict(),
                "CASENUM": casenum,
                "DTFILED": (
                        datetime.strptime(dtfiled, "%Y-%m-%d").strftime("%B %d, %Y")
                        if dtfiled else None
                    )
            }
            for record, casenum, dtfiled in records
        ]
    })