from flask import Blueprint, render_template, jsonify, request, redirect
from flask_login import login_required
from app.routes.decorators import require_module
from app.models import CTMS1000, CTMS4100, CTMS4000, CTMS2310, CTMS2300
from app import db
from datetime import datetime

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



@criminals_bp.route('/add')
@login_required
def add_case_form():

    # =========================
    # NATURES (CUSTOM ORDER)
    # =========================
    natures_raw = (
        CTMS2310.query
        .filter_by(CATEGORY='5')
        .all()
    )

    nature_order = [32, 30, 36, 35, 29, 28, 31, 27, 34, 33]

    natures = sorted(
        natures_raw,
        key=lambda x: nature_order.index(int(x.NATURECODE)) if int(x.NATURECODE) in nature_order else 999
    )

    # =========================
    # CSTATUS (CUSTOM ORDER)
    # =========================
    cstatus_raw = (
        CTMS2300.query
        .filter_by(CATEGORY='STATUS')
        .all()
    )

    status_order = [120, 20, 140, 130, 10, 90, 40, 80, 30, 60, 70, 110, 100]

    cstatus = sorted(
        cstatus_raw,
        key=lambda x: status_order.index(int(x.CODEID)) if int(x.CODEID) in status_order else 999
    )



    case_cat =  (
        CTMS2300.query
        .filter_by(CATEGORY='CATEGORY')
        .all()
    )

    return render_template(
        'civil_cases/cc_create.html',
        natures=natures,
        cstatus=cstatus,
        case_cat=case_cat
    )

@criminals_bp.route('/add-case', methods=['POST'])
@login_required
def add_case():

    # =========================
    # 1. GET LAST CASEID + 1
    # =========================
    last_case = (
        db.session.query(CTMS1000.CASEID)
        .order_by(CTMS1000.CASEID.desc())
        .first()
    )

    next_case_id = (last_case[0] + 1) if last_case and last_case[0] else 1


    # =========================
    # 2. FORCE COURTID = 2088
    # =========================
    COURT_ID_FIXED = 2088
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    CREATEDT=now,
    MODIFYDT=now,

    # =========================
    # 3. CREATE NEW CASE
    # =========================
    new_case = CTMS1000(
        CASEID=next_case_id,   # MANUAL INCREMENT
        COURTID=COURT_ID_FIXED,
        NATURECODE=request.form.get('NATURECODE').zfill(5),
        CATEGORY='00005',
        CASENUM=request.form.get('CASENUM'),
        CASETITLE=request.form.get('CASETITLE'),
        DTFILED=request.form.get('DTFILED'),
        DTRECEIVED=request.form.get('DTRECEIVED'),
        CASETYPE="CR",
        NATUREREM = request.form.get('NATUREREM').upper(),
        IAMOUNT = 0.0,
        IWEIGHT = 0.0,
        CSTATUSID = request.form.get('CSTATUSID').zfill(5),
        CSTATUS=request.form.get('satusOthers'),
        CLOSESTAT='10006',
        CREATEBY="BCC1",
        MODIFYBY="BCC1",
        CREATEDT=now,
        MODIFYDT=now,
    )

    db.session.add(new_case)
    db.session.commit()

    return redirect('/cc')


@criminals_bp.route('/add_person/<int:case_id>')
@login_required
def add_person_form(case_id):
    return render_template(
        'civil_cases/add_person.html',
        case_id=case_id
    )



@criminals_bp.route('/save_person', methods=['POST'])
@login_required
def save_person():

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # =========================
    # 1. GET NEXT PERSONID
    # =========================
    last_person = db.session.query(CTMS4000.PERSONID)\
        .order_by(CTMS4000.PERSONID.desc()).first()

    next_person_id = (last_person[0] + 1) if last_person else 1

    # =========================
    # 2. CREATE PERSON
    # =========================
    person = CTMS4000(
        PERSONID=next_person_id,
        FNAME=request.form.get('FNAME').upper(),
        MNAME=request.form.get('MNAME').upper() if request.form.get('MNAME') else None,
        LNAME=request.form.get('LNAME').upper(),
        CREATEBY="BCC1",
        CREATEDT=now
    )

    db.session.add(person)
    db.session.flush()  # important to use PERSONID immediately

    # =========================
    # 3. GET NEXT PARTYID
    # =========================
    last_party = db.session.query(CTMS4100.PARTYID)\
        .order_by(CTMS4100.PARTYID.desc()).first()

    next_party_id = (last_party[0] + 1) if last_party else 1

    # =========================
    # 4. CREATE PARTY (LINK)
    # =========================
    party = CTMS4100(
        PARTYID=next_party_id,
        CASEID=request.form.get('CASEID'),
        PERSONID=person.PERSONID,

        DETAINED=2,
        PLEA=0,
        PPOSTPONED=0,
        DPOSTPONED=0,
        DISPOSCODE=0,
        AGECOMIT=0,

        CREATEBY="BCC1",
        CREATEDT=now,
        MODIFYBY="BCC1",
        MODIFYDT=now
    )

    db.session.add(party)
    db.session.commit()

    return redirect('/cc')