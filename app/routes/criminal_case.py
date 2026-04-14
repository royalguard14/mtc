from flask import Blueprint, render_template, jsonify, request, redirect
from flask_login import login_required
from app.routes.decorators import require_module
from app.models import CTMS1000, CTMS4100, CTMS4000, CTMS2310, CTMS2300
from app import db
from datetime import datetime
from app.routes.helpers import touch_case, get_now, CURRENT_USER
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
    pStatus = [
        "AT-LARGE",
        "BONDED",
        "ESCAPED FROM PRISON",
        "DETAINED",
        "JUMPED BAIL",
        "OUT ON BAIL",
        "REHABILITATION",
        "RELEASED ON RECOGNIZANCE",
        "UNDER PROBATION"
    ]
    rfrs_raw = (
        CTMS2300.query
        .filter_by(CATEGORY='RELEASED')
        .all()
    )
    rfrs_order = [20001,20002,20003,20004,20005,20006,20007,20008,20009]
    rfrs = sorted(
        rfrs_raw,
        key=lambda x: rfrs_order.index(int(x.CODEID)) if int(x.CODEID) in rfrs_order else 999
    )
    decisions_raw = (
        CTMS2300.query
        .filter_by(CATEGORY='DECISION')
        .all()
    )
    decisions_order = [90001, 90002, 90003]
    decisions = sorted(
        decisions_raw,
        key=lambda x: (
            decisions_order.index(int(x.CODEID))
            if int(x.CODEID) in decisions_order
            else 999
        )
    )
    return render_template(
        'civil_cases/person_view.html',
        party=party,
        person=party.person,
        case=party.case,
        pStatus=pStatus,
        rfrs=rfrs,
        decisions=decisions
    )





@criminals_bp.route('/update-person/<int:person_id>', methods=['POST'])
@login_required
def update_person(person_id):
    person = CTMS4000.query.get_or_404(person_id)
    form = request.form
    now = get_now()
# I-Personal Infp
    person.FNAME = form.get('FNAME', '').upper()
    person.MNAME = form.get('MNAME', '').upper()
    person.LNAME = form.get('LNAME', '').upper()
    person.ANAME = form.get('ANAME', '').upper()
    person.GENDER = form.get('GENDER')
    person.DBIRTH = form.get('DBIRTH')
    person.TELNO = form.get('TELNO')
    person.PSTATUS = form.get('PSTATUS')
    person.ADDRESS1 = form.get('ADDRESS1')
    person.MODIFYDT = now
    person.MODIFYBY = CURRENT_USER
    # 🔥 UPDATE ALL RELATED CASES
    parties = CTMS4100.query.filter_by(PERSONID=person.PERSONID).all()
    for p in parties:
        touch_case(p.CASEID)
    party = CTMS4100.query.filter_by(PERSONID=person.PERSONID).first()
    if party:
        party.AGECOMIT = form.get('AGECOMIT')
# II-arrainment and pre trrial
        party.DETAINED = form.get('DETAINED')
        party.DTDETAINED = form.get('DTDETAINED')
        party.DTARREST = form.get('DTARREST')
        party.DTBAIL = form.get('DTBAIL')
        party.DTSURRENDR = form.get('DTSURRENDR')
        party.BAILREM = form.get('BAILREM')
        party.DTRELEASED = form.get('DTRELEASED')
        party.RELEASED = form.get('RELEASED')
# III-mediation
        party.DTREFERRED = form.get('DTREFERRED')
        party.DTRETURNED = form.get('DTRETURNED')
        party.MEDIATION = form.get('MEDIATION')
# IV-PE
        party.DTSETTING = form.get('DTSETTING')
        party.DTINITIAL = form.get('DTINITIAL')
        party.DTLAST = form.get('DTLAST')
        party.PPOSTPONED = form.get('PPOSTPONED')
        party.DTOFFERPRO = form.get('DTOFFERPRO')
        party.DTDEMURRER = form.get('DTDEMURRER')
# V-DE
        party.DTDEFENSE = form.get('DTDEFENSE')
        party.DTACTUAL = form.get('DTACTUAL')
        party.DTLTTRIAL = form.get('DTLTTRIAL')
        party.DPOSTPONED = form.get('DPOSTPONED')
        party.DTOFFERDEF = form.get('DTOFFERDEF')
        party.DTREBUTTAL = form.get('DTREBUTTAL')
        party.DTSURREBUT = form.get('DTSURREBUT')
# VI-DEsison
        party.DTSUBMIT = form.get('DTSUBMIT')
        party.DTPROMUL = form.get('DTPROMUL')
        party.DECIDECODE = form.get('DECIDECODE')
        party.PENALTY = form.get('PENALTY')
        party.REMARKS = form.get('REMARKS')
        party.MODIFYDT = now
        party.MODIFYBY = CURRENT_USER
        touch_case(party.CASEID)
    db.session.commit()
    return {
        "status": "success",
        "data": person.to_dict()
    }





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
    pStatus = [
        "AT-LARGE",
        "BONDED",
        "ESCAPED FROM PRISON",
        "DETAINED",
        "JUMPED BAIL",
        "OUT ON BAIL",
        "REHABILITATION",
        "RELEASED ON RECOGNIZANCE",
        "UNDER PROBATION"
    ]
    return render_template(
        'civil_cases/add_person.html',
        case_id=case_id,
        pStatus=pStatus
    )





@criminals_bp.route('/save_person', methods=['POST'])
@login_required
def save_person():
    now = datetime.now().isoformat(timespec='microseconds')
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
        ANAME=request.form.get('ANAME').upper(),
        DBIRTH= request.form.get('DBIRTH'),
        GENDER=request.form.get('GENDER'),
        ADDRESS1=request.form.get('ADDRESS1'),
        TELNO=request.form.get('TELNO'),
        PSTATUS=request.form.get('PSTATUS'),
        STATCASEID=0,
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
        AGECOMIT=request.form.get('AGECOMIT'),
        CREATEBY="BCC1",
        CREATEDT=now,
        MODIFYBY="BCC1",
        MODIFYDT=now
    )
    db.session.add(party)
    db.session.commit()
    return redirect('/cc')