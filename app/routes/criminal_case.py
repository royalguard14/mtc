from flask import Blueprint, render_template, jsonify, request, redirect, Response
from flask_login import login_required
from app.routes.decorators import require_module
from app.models import CTMS1000, CTMS4100, CTMS4000, CTMS2310, CTMS2300, CTMS9000
from app import db
from datetime import datetime, timedelta
from app.routes.helpers import touch_case, get_now, CURRENT_USER, run_dbf_sync
from sqlalchemy.orm import joinedload
import csv
from io import StringIO
from sqlalchemy import or_, and_
import tempfile
import dbf






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

    run_dbf_sync()
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
        .filter_by(CATEGORY='00005')
        .all()
    )




    nature_order = ["00032", "00030", "00036", "00035", "00029", "00028", "00031", "00027", "00034", "00033"]
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

    run_dbf_sync()

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
    run_dbf_sync()
    return redirect('/cc')



@criminals_bp.route('/report-email')
@login_required
def generate_report():

    from_month = request.args.get('from')
    to_month = request.args.get('to')

    if not from_month or not to_month:
        return {"error": "Missing date range"}, 400

    from_date = datetime.strptime(from_month, "%Y-%m")
    to_date = datetime.strptime(to_month, "%Y-%m")

    # next month fix
    if to_date.month == 12:
        to_date = to_date.replace(year=to_date.year + 1, month=1)
    else:
        to_date = to_date.replace(month=to_date.month + 1)

    from_str = from_date.strftime("%Y-%m-%d")
    to_str = to_date.strftime("%Y-%m-%d")

    # =====================================================
    # QUERY
    # =====================================================

    case_rows = CTMS1000.query.filter(
        or_(
            and_(CTMS1000.CREATEDT >= from_str, CTMS1000.CREATEDT < to_str),
            and_(CTMS1000.MODIFYDT >= from_str, CTMS1000.MODIFYDT < to_str)
        )
    ).order_by(CTMS1000.CASEID).options(joinedload(CTMS1000.parties)).all()

    party_rows = CTMS4100.query.filter(
        or_(
            and_(CTMS4100.CREATEDT >= from_str, CTMS4100.CREATEDT < to_str),
            and_(CTMS4100.MODIFYDT >= from_str, CTMS4100.MODIFYDT < to_str)
        )
    ).order_by(CTMS4100.CASEID).all()

    person_rows = CTMS4000.query.filter(
        CTMS4000.CREATEDT >= from_str,
        CTMS4000.CREATEDT < to_str
    ).order_by(CTMS4000.PERSONID).all()


    # # =====================================================
    # # CLEAR TABLE
    # # =====================================================
    CTMS9000.query.delete()
    db.session.commit()

    

    # # =====================================================
    # # INSERT CASES
    # # =====================================================
    case_records = []

    for c in case_rows:
        rec = CTMS9000(
            # CASE ONLY
            CASEID=c.CASEID,
            COURTID=c.COURTID,
            NATURECODE=c.NATURECODE,
            CATEGORY=c.CATEGORY,
            CASENUM=c.CASENUM,
            CASETITLE=c.CASETITLE,

            DTFILED=c.DTFILED,
            DTRECEIVED=c.DTRECEIVED,
            DTTRANSFER=c.DTTRANSFER,
            TRANSFER=c.TRANSFER,

            CASETYPE=c.CASETYPE,
            CLOSEDATE=c.CLOSEDATE,
            CLOSETAG=c.CLOSETAG,
            CLOSEDET=c.CLOSEDET,
            CLOSESTAT=c.CLOSESTAT,

            NATUREREM=c.NATUREREM,
            IAMOUNT=c.IAMOUNT,
            IWEIGHT=c.IWEIGHT,

            CSTATUS=c.CSTATUS,
            CSTATUSID=c.CSTATUSID,

            CREATEBY=c.CREATEBY,
            CREATEDT=c.CREATEDT.split("T")[0] if c.CREATEDT else None,
            MODIFYBY=c.MODIFYBY,
            MODIFYDT=c.MODIFYDT.split("T")[0] if c.MODIFYDT else None,

            PERSONID=int(0),
            PARTYID=int(0),
            DISPOSCODE=int(0),

            EXPORTTAG="CASEMAST"
        )
        db.session.add(rec)
        




    # =====================================================
    # INSERT PARTY (ONLY ONCE)
    # =====================================================
    for p in party_rows:

        rec = CTMS9000(
            AGECOMIT = p.AGECOMIT,
            BAILREM = p.BAILREM,
            CASEID = p.CASEID,
            COURTID =0,
            CREATEBY = p.CREATEBY,
            CREATEDT=c.CREATEDT.split("T")[0] if c.CREATEDT else None,
            DECIDECODE = p.DECIDECODE,
            DETAINED = p.DETAINED,
            DISPOSCODE = p.DISPOSCODE,
            DPOSTPONED = p.DPOSTPONED,
            DTACTUAL = p.DTACTUAL,
            DTARCHIVED = p.DTARCHIVED,
            DTARRAIGN = p.DTARRAIGN,
            DTARREST = p.DTARREST,
            DTBAIL = p.DTBAIL,
            DTDEFENSE = p.DTDEFENSE,
            DTDEMURRER = p.DTDEMURRER,
            DTDETAINED = p.DTDETAINED,
            DTIARRAIGN = p.DTIARRAIGN,
            DTINITIAL = p.DTINITIAL,
            DTLAST = p.DTLAST,
            DTLTTRIAL = p.DTLTTRIAL,
            DTOFFERDEF = p.DTOFFERDEF,
            DTOFFERPRO = p.DTOFFERPRO,
            DTPLEA = p.DTPLEA,
            DTPRETRIAL = p.DTPRETRIAL,
            DTPROMUL = p.DTPROMUL,
            DTREBUTTAL = p.DTREBUTTAL,
            DTREFERRED = p.DTREFERRED,
            DTRELEASED = p.DTRELEASED,
            DTRETURNED = p.DTRETURNED,
            DTREVIVED = p.DTREVIVED,
            DTSENTENCE = p.DTSENTENCE,
            DTSETTING = p.DTSETTING,
            DTSUBMIT = p.DTSUBMIT,
            DTSURREBUT = p.DTSURREBUT,
            DTSURRENDR = p.DTSURRENDR,
            JRENDERED = p.JRENDERED,
            MEDIATION = p.MEDIATION,
            MODIFYBY = p.MODIFYBY,
            MODIFYDT=p.MODIFYDT.split("T")[0] if p.MODIFYDT else None,
            PARTYID = p.PARTYID,
            PBARGAIN = p.PBARGAIN,
            PENALTY = p.PENALTY,
            PERSONID = p.PERSONID,
            PLEA = p.PLEA,
            PPOSTPONED = p.PPOSTPONED,
            PSTATUS = p.PSTATUS,
            RELEASED = p.RELEASED,
            REMARKS = p.REMARKS,

            EXPORTTAG="CPARTY"
        )

        db.session.add(rec)

    # =====================================================
    # INSERT PERSON (ONLY ONCE)
    # =====================================================
    for per in person_rows:

        rec = CTMS9000(
            ADDRESS1 = per.ADDRESS1,
            ADDRESS2 = per.ADDRESS2,
            ADDRESS3 = per.ADDRESS3,
            ANAME = per.ANAME,
            CASEID =0,
            COURTID =0,
            CREATEBY = per.CREATEBY,
            CREATEDT = per.CREATEDT,
            DBIRTH = per.DBIRTH,
            FNAME = per.FNAME,
            GENDER = per.GENDER,
            LNAME = per.LNAME,
            MNAME = per.MNAME,
            PARTYID =0,
            PERSONID = per.PERSONID,
            PSTATUS = per.PSTATUS,
            TELNO = per.TELNO,




            DISPOSCODE = 0,

            EXPORTTAG="PERSON"
        )

        db.session.add(rec)

    # =====================================================
    # COMMIT ONCE
    # =====================================================
    db.session.commit()
    # =========================
    # HEADER (UNCHANGED)
    # =========================
    CSV_FIELDS = [
        "CASEID","COURTID","PERSONID","PARTYID",
        "NATURECODE,C,5","NATUREDESC,C,150","CATEGORY,C,5","CATEGDESC,C,100",
        "CASENUM,C,80","CASETITLE,C,250",
        "DTFILED,D","DTRECEIVED,D","DTTRANSFER,D",
        "TRANSFER,N,1,0","CASETYPE,C,2","CRTTYPE,C,4",
        "CLOSEDATE,D","CLOSETAG,C,1","CLOSEDET,C,200",
        "CLOSESTAT,C,5","CLOSEDESC,C,50","NATUREREM,C,200",
        "IAMOUNT,N,20,2","IWEIGHT,N,20,5",
        "CSTATUS,C,100","CSTATUSID,C,5","CSTATDESC,C,100",
        "ENAME,C,5","FNAME,C,80","LNAME,C,80","MNAME,C,40",
        "DBIRTH,D","GENDER,C,1",
        "ADDRESS1,C,200","ADDRESS2,C,200","ADDRESS3,C,200",
        "TELNO,C,200","PSTATUS,C,30",
        "AGE,N,3,0","DETAINED,N,1,0",
        "DTIARRAIGN,D","DTPRETRIAL,D","DTARRAIGN,D",
        "PLEA,N,1,0","PBARGAIN,N,1,0","JRENDERED,N,1,0",
        "DTSETTING,C,100","DTINITIAL,D","DTLAST,D",
        "DTOFFERPRO,D","DTDEMURRER,D","DTDEFENSE,C,100",
        "DTACTUAL,D","DTLTTRIAL,D",
        "PPOSTPONED,N,5,0","DPOSTPONED,N,5,0",
        "DTOFFERDEF,D","DTREBUTTAL,D","DTSURREBUT,D",
        "DTSUBMIT,D","DTPROMUL,D",
        "DISPOSCODE","DISPOSDESC,C,100",
        "PENALTY,C,250","REMARKS,C,250",
        "DTPLEA,D","DTSENTENCE,D","DTARCHIVED,D",
        "DTREFERRED,D","DTRETURNED,D",
        "AGECOMIT,N,3,0","DTDETAINED,D","DECIDECODE,C,5",
        "ANAME,C,100","DTREVIVED,D",
        "CASETAG,C,20","REASON,C,100","CASENUMOLD,C,80",
        "DTBAIL,D","MEDIATION,C,1",
        "DISPOSEDES,C,100","BAILREM,C,100",
        "DTSURRENDR,D","DTARREST,D","DTRELEASED,D",
        "RELEASED,C,5","RELEASEDES,C,100",
        "AGEING_Y,N,5,0","AGEING_M,N,5,0","AGEING_D,N,5,0","AGEING_T,N,12,0",
        "AGEING_DES,C,100",
        "CREATEBY,C,4","CREATEDT,D","MODIFYDT","MODIFYBY,C,4",
        "EXPORTTAG,C,10"
    ]

    # =========================
    # FIELD MAP
    # =========================
    FIELD_MAP = {f: f.split(",")[0] for f in CSV_FIELDS}

    # =========================
    # EXPORT
    # =========================
    output = StringIO()
    writer = csv.writer(output)

    # header
    writer.writerow(CSV_FIELDS)

    records = CTMS9000.query.order_by(CTMS9000.id).all()

    for r in records:
        row = []

        for col in CSV_FIELDS:
            field = FIELD_MAP.get(col)
            value = getattr(r, field, "") if field else ""

            if value is None:
                value = ""

            row.append(str(value))  # NO truncation

        writer.writerow(row)

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ctms9000.csv"}
    )




    # return {
    #     "status": "success",
    #     "data": [r.to_dict() for r in records]
        
    # }




