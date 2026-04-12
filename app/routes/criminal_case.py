from flask import Blueprint, render_template, jsonify, request, redirect
from flask_login import login_required
from app.routes.decorators import require_module
from app.models import CTMS1000, CTMS4100, CTMS4000
from app import db

from sqlalchemy.orm import joinedload

criminals_bp = Blueprint('criminals', __name__, url_prefix='/cc')


# =========================
# MAIN PAGE
# =========================
@criminals_bp.route('/')
@login_required
@require_module(9)
def criminal():

    cases = (
        CTMS1000.query
        .options(
            joinedload(CTMS1000.parties)
            .joinedload(CTMS4100.person)
        )
        .all()
    )

    return render_template(
        'civil_cases/cc_index.html',
        criminal_records=cases
    )


# =========================
# FULL CASE DETAILS (PRO)
# =========================
@criminals_bp.route('/case-details/<int:case_id>')
@login_required
def case_details(case_id):

    case = (
        CTMS1000.query
        .options(
            joinedload(CTMS1000.parties)
            .joinedload(CTMS4100.person)
        )
        .get_or_404(case_id)
    )

    def to_dict(obj):
        """Convert SQLAlchemy object to full dict"""
        return {
            c.name: getattr(obj, c.name)
            for c in obj.__table__.columns
        }

    return jsonify({
        "case": to_dict(case),

        "parties": [
            {
                **to_dict(p),
                "PERSONID": p.PERSONID,

                "person": to_dict(p.person) if p.person else None,

                # formatted name (safe + middle initial)
                "FULLNAME": (
                    f"{p.person.FNAME} "
                    f"{(p.person.MNAME[0] + '.') if p.person.MNAME else ''} "
                    f"{p.person.LNAME}"
                ).strip() if p.person else p.PARTYNAME
            }
            for p in case.parties
        ]
    })


@criminals_bp.route('/person/<int:person_id>')
@login_required
def view_person(person_id):

    party = (
        CTMS4100.query
        .options(
            joinedload(CTMS4100.person),
            joinedload(CTMS4100.case)
        )
        .filter_by(PERSONID=person_id)
        .first_or_404()
    )

    return render_template(
        'civil_cases/person_view.html',
        party=party,
        person=party.person,
        case=party.case
    )





@criminals_bp.route('/update-person/<int:person_id>', methods=['POST'])
@login_required
def update_person(person_id):

    person = CTMS4000.query.get_or_404(person_id)

    # PERSON FIELDS
    person.FNAME = request.form.get('FNAME')
    person.MNAME = request.form.get('MNAME')
    person.LNAME = request.form.get('LNAME')
    person.GENDER = request.form.get('GENDER')
    person.ADDRESS1 = request.form.get('ADDRESS1')

    # PARTY FIELDS (if needed)
    party = CTMS4100.query.filter_by(PERSONID=person_id).first()
    if party:
        party.DTARRAIGN = request.form.get('DTARRAIGN')
        party.DTPRETRIAL = request.form.get('DTPRETRIAL')
        party.DTINITIAL = request.form.get('DTINITIAL')
        party.DTLAST = request.form.get('DTLAST')

        party.MEDIATION = request.form.get('MEDIATION')
        party.DTOFFERPRO = request.form.get('DTOFFERPRO')
        party.DTACTUAL = request.form.get('DTACTUAL')
        party.DTOFFERDEF = request.form.get('DTOFFERDEF')
        party.DTDEFENSE = request.form.get('DTDEFENSE')
        party.DTPROMUL = request.form.get('DTPROMUL')
        party.PENALTY = request.form.get('PENALTY')

    db.session.commit()

    return redirect(request.referrer)
