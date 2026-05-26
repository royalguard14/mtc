
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
            TRANSFER = None if (c.TRANSFER is None or c.TRANSFER == 0) else c.TRANSFER,


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
            MODIFYDT = (datetime.fromisoformat(c.MODIFYDT).strftime("%m/%d/%Y %H:%M:%S") if c.MODIFYDT else None),

            PERSONID=int(0),
            PARTYID=int(0),
            DISPOSCODE=int(0),

            EXPORTTAG="CASEMAST"
        )
        db.session.add(rec)
        db.session.commit()  
        




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
            MODIFYDT = (datetime.fromisoformat(c.MODIFYDT).strftime("%m/%d/%Y %H:%M:%S") if c.MODIFYDT else None),
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
        db.session.commit()  

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
        db.session.commit()  


    # =====================================================
    # settings
    # =====================================================
    sets = SettingsCTMS.query.first()

    if sets:
        rec = CTMS9000(
            CASEID = sets.COURTID,
            COURTID = 0,
            PERSONID = 0,
            PARTYID = 0,
            CRTTYPE = sets.CRTTYPE,

            MODIFYDT = datetime.strptime(sets.MODIDT, "%Y-%m-%d").strftime("%m/%d/%y %I:%M %p"),
            DETAINED = sets.ISSINGLE,
            DISPOSCODE = 0,
            EXPORTTAG = "SETTINGS"
        )

        db.session.add(rec)
        db.session.commit()


    court = CTMS2100.query.filter_by(COURTID=1700).first()
    if court:
        rec = CTMS9000(
            CASEID = sets.COURTID,
            COURTID = 0,
            PERSONID = 0,
            PARTYID = 0,
            CRTTYPE = sets.CRTTYPE,

            CSTATUSID = court.REGION,
            ENAME = "001",

            ADDRESS1 =  court.PLACEASS,
            ADDRESS2 = court.PLACEASS2,

            DISPOSCODE = 0,
            DECIDECODE = court.TOWN ,
            
            EXPORTTAG = "COURTCD"
        )

        db.session.add(rec)
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
    # BUILD DBF STRUCTURE
    # =========================
    field_defs = []
    field_names = []
    field_types = {}   # store type info for conversion

    for f in CSV_FIELDS:
        parts = f.split(",")

        name = parts[0][:10]  # DBF limit
        field_names.append(name)

        if len(parts) == 1:
            field_defs.append(f"{name} C(255)")
            field_types[name] = ("C", 255)

        else:
            ftype = parts[1]

            if ftype == "C":
                size = int(parts[2])
                field_defs.append(f"{name} C({size})")
                field_types[name] = ("C", size)

            elif ftype == "N":
                size = int(parts[2])
                dec = int(parts[3])
                field_defs.append(f"{name} N({size},{dec})")
                field_types[name] = ("N", size, dec)

            elif ftype == "D":
                field_defs.append(f"{name} D")
                field_types[name] = ("D",)

            else:
                field_defs.append(f"{name} C(255)")
                field_types[name] = ("C", 255)

    structure = "; ".join(field_defs)

    # =========================
    # CREATE TEMP DBF
    # =========================
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".dbf")
    tmp.close()

    table = dbf.Table(tmp.name, structure, codepage='cp1252')
    table.open(mode=dbf.READ_WRITE)

    # =========================
    # EXPORT DATA
    # =========================
    records = CTMS9000.query.order_by(CTMS9000.id).all()

    for r in records:
        row_data = {}

        for original, name in zip(CSV_FIELDS, field_names):
            field = original.split(",")[0]
            value = getattr(r, field, None)

            ftype = field_types[name][0]

            # =========================
            # TYPE HANDLING
            # =========================
            if value is None:
                if ftype == "N":
                    value = None
                elif ftype == "D":
                    value = None
                else:
                    value = ""

            # # CHARACTER
            # if ftype == "C":
            #         max_len = field_types[name][1]
            #         value = safe_str(value, max_len)

            if ftype == "C":
                value = "" if value is None else str(value)
                max_len = field_types[name][1]
                value = value[:max_len]

            # NUMERIC
            elif ftype == "N":
                if value is None or value == "":
                    value = None   # IMPORTANT: keep NULL
                else:
                    try:
                        value = float(value)
                    except:
                        value = None

            # DATE
            elif ftype == "D":
                if isinstance(value, datetime):
                    value = value.date()
                elif isinstance(value, str):
                    try:
                        value = datetime.strptime(value[:10], "%Y-%m-%d").date()
                    except:
                        value = None

            row_data[name] = value

        table.append(row_data)

    table.close()

    # =========================
    # RESPONSE
    # =========================
    with open(tmp.name, "rb") as f:
        dbf_data = f.read()

    os.unlink(tmp.name)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"CTMS{timestamp}.dbf"

    return Response(
        dbf_data,
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}

    )
    

    # return {
    #     "status": "success",
    #     "data": [r.to_dict() for r in records]
        
    # }


