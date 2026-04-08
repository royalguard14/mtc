from . import db  # ✅ relative import avoids the loop


from datetime import datetime
from flask_login import UserMixin

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(255), nullable=False)
    modules = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)

    isDeleted = db.Column(db.Boolean, default=False)
    isActive = db.Column(db.Boolean, default=True)

    remember_token = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete")


class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    nationality = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    function_desc = db.Column(db.String(255), nullable=False)
    function = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('frontend', 'backend', name='setting_type'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Region(db.Model):
    __tablename__ = 'table_region'

    region_id = db.Column(db.Integer, primary_key=True)
    region_name = db.Column(db.String(50), unique=True, index=True, nullable=False)
    region_description = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    provinces = db.relationship('Province', back_populates='region', cascade="all, delete")


class Province(db.Model):
    __tablename__ = 'table_province'

    province_id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('table_region.region_id', ondelete='CASCADE'), index=True, nullable=False)
    province_name = db.Column(db.String(100), nullable=False, index=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('region_id', 'province_name', name='UQT_provincename'),
    )

    region = db.relationship('Region', back_populates='provinces')
    municipalities = db.relationship('Municipality', back_populates='province', cascade="all, delete")


class Municipality(db.Model):
    __tablename__ = 'table_municipality'

    municipality_id = db.Column(db.Integer, primary_key=True)
    province_id = db.Column(db.Integer, db.ForeignKey('table_province.province_id', ondelete='SET NULL'), index=True, nullable=True)
    municipality_name = db.Column(db.String(100), index=True, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('province_id', 'municipality_name', name='UQT_municipality'),
    )

    province = db.relationship('Province', back_populates='municipalities')
    barangays = db.relationship('Barangay', back_populates='municipality', cascade="all, delete-orphan")


class Barangay(db.Model):
    __tablename__ = 'table_barangay'

    barangay_id = db.Column(db.Integer, primary_key=True)
    municipality_id = db.Column(db.Integer, db.ForeignKey('table_municipality.municipality_id', ondelete='CASCADE'), nullable=False)
    barangay_name = db.Column(db.String(100), nullable=False, index=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('municipality_id', 'barangay_name', name='UQT_barangay'),
    )

    municipality = db.relationship('Municipality', back_populates='barangays')



# =========================
# CTMS TABLES
# =========================

class CTMS2320(db.Model):
    __tablename__ = 'CTMS2320'

    DISPOSCODE = db.Column(db.Integer, primary_key=True)
    DESCRP = db.Column(db.Text)
    CREATEDT = db.Column(db.Text)
    CREATEBY = db.Column(db.Text)


class CTMS3200(db.Model):
    __tablename__ = 'CTMS3200'

    LOGID = db.Column(db.Integer, primary_key=True)
    LOGDATE = db.Column(db.Text)
    LOGTIME = db.Column(db.Text)
    USERID = db.Column(db.Text)
    MODULE = db.Column(db.Text)
    ACTION = db.Column(db.Text)
    EMPNUM = db.Column(db.Text)
    PTAG = db.Column(db.Integer)


class TCOURT(db.Model):
    __tablename__ = 'TCOURT'

    CRTTYPE = db.Column(db.Text, primary_key=True)
    CRTDESC = db.Column(db.Text)


class TREGION(db.Model):
    __tablename__ = 'TREGION'

    REG_CODE = db.Column(db.Text, primary_key=True)
    REG_DESC = db.Column(db.Text)


class CTMS3100(db.Model):
    __tablename__ = 'ctms3100'

    USERID = db.Column(db.Text, primary_key=True)
    USERNAME = db.Column(db.Text)
    USERDESIG = db.Column(db.Text)
    USERPASS = db.Column(db.Text)
    LASTLOGIN = db.Column(db.Text)
    LASTPW = db.Column(db.Text)
    PTAG = db.Column(db.Integer)


class CTMS4000(db.Model):
    __tablename__ = 'ctms4000'

    PERSONID = db.Column(db.Integer, primary_key=True)
    ENAME = db.Column(db.Text)
    FNAME = db.Column(db.Text)
    LNAME = db.Column(db.Text)
    MNAME = db.Column(db.Text)
    ANAME = db.Column(db.Text)
    DBIRTH = db.Column(db.Text)
    GENDER = db.Column(db.Text)
    ADDRESS1 = db.Column(db.Text)
    ADDRESS2 = db.Column(db.Text)
    ADDRESS3 = db.Column(db.Text)
    TELNO = db.Column(db.Text)
    PSTATUS = db.Column(db.Text)
    STATCASEID = db.Column(db.Integer)
    CREATEBY = db.Column(db.Text)
    CREATEDT = db.Column(db.Text)


class CTMS1000(db.Model):
    __tablename__ = 'ctms1000'

    CASEID = db.Column(db.Integer, primary_key=True)
    COURTID = db.Column(db.Integer)
    NATURECODE = db.Column(db.Text)
    CATEGORY = db.Column(db.Text)
    CASENUM = db.Column(db.Text)
    CASETITLE = db.Column(db.Text)
    DTFILED = db.Column(db.Text)
    DTRECEIVED = db.Column(db.Text)
    DTTRANSFER = db.Column(db.Text)
    TRANSFER = db.Column(db.Integer)
    CASETYPE = db.Column(db.Text)
    CLOSEDATE = db.Column(db.Text)
    CLOSETAG = db.Column(db.Text)
    CLOSEDET = db.Column(db.Text)
    NATUREREM = db.Column(db.Text)
    IAMOUNT = db.Column(db.Float)
    IWEIGHT = db.Column(db.Float)
    CSTATUS = db.Column(db.Text)
    CSTATUSID = db.Column(db.Text)
    CLOSESTAT = db.Column(db.Text)
    CREATEBY = db.Column(db.Text)
    CREATEDT = db.Column(db.Text)
    MODIFYBY = db.Column(db.Text)
    MODIFYDT = db.Column(db.Text)


class CTMS2100(db.Model):
    __tablename__ = 'ctms2100'

    COURTID = db.Column(db.Integer, primary_key=True)
    CRTTYPE = db.Column(db.Text)
    REGION = db.Column(db.Text)
    BRANCH = db.Column(db.Text)
    TOWN = db.Column(db.Text)
    PLACEASS = db.Column(db.Text)
    PLACEASS2 = db.Column(db.Text)
    ORDER = db.Column(db.Integer)
    ON = db.Column(db.Text)
    CITYTOWN = db.Column(db.Text)


class CTMS2310(db.Model):
    __tablename__ = 'ctms2310'

    NATURECODE = db.Column(db.Text, primary_key=True)
    CATEGORY = db.Column(db.Text)
    NATUREDESC = db.Column(db.Text)
    CRTTYPE = db.Column(db.Text)
    CREATEBY = db.Column(db.Text)
    CREATEDT = db.Column(db.Text)


class CTMS4100(db.Model):
    __tablename__ = 'ctms4100'

    PARTYID = db.Column(db.Integer, primary_key=True)
    CASEID = db.Column(db.Integer)
    PERSONID = db.Column(db.Integer)
    PSTATUS = db.Column(db.Text)
    PARTYNAME = db.Column(db.Text)
    DETAINED = db.Column(db.Integer)
    DTIARRAIGN = db.Column(db.Text)
    DTPRETRIAL = db.Column(db.Text)
    DTARRAIGN = db.Column(db.Text)
    PLEA = db.Column(db.Integer)
    PBARGAIN = db.Column(db.Integer)
    JRENDERED = db.Column(db.Integer)
    DTSETTING = db.Column(db.Text)
    DTINITIAL = db.Column(db.Text)
    DTLAST = db.Column(db.Text)
    DTOFFERPRO = db.Column(db.Text)
    DTDEMURRER = db.Column(db.Text)
    DTDEFENSE = db.Column(db.Text)
    DTACTUAL = db.Column(db.Text)
    DTLTTRIAL = db.Column(db.Text)
    PPOSTPONED = db.Column(db.Integer)
    DPOSTPONED = db.Column(db.Integer)
    DTOFFERDEF = db.Column(db.Text)
    DTREBUTTAL = db.Column(db.Text)
    DTSURREBUT = db.Column(db.Text)
    DTSUBMIT = db.Column(db.Text)
    DTPROMUL = db.Column(db.Text)
    DISPOSCODE = db.Column(db.Integer)
    PENALTY = db.Column(db.Text)
    REMARKS = db.Column(db.Text)
    DTPLEA = db.Column(db.Text)
    DTSENTENCE = db.Column(db.Text)
    DTARCHIVED = db.Column(db.Text)
    DTREFERRED = db.Column(db.Text)
    DTRETURNED = db.Column(db.Text)
    AGECOMIT = db.Column(db.Integer)
    DTDETAINED = db.Column(db.Text)
    DECIDECODE = db.Column(db.Text)
    DTREVIVED = db.Column(db.Text)
    MEDIATION = db.Column(db.Text)
    DTARREST = db.Column(db.Text)
    DTSURRENDR = db.Column(db.Text)
    DTBAIL = db.Column(db.Text)
    BAILREM = db.Column(db.Text)
    DTRELEASED = db.Column(db.Text)
    RELEASED = db.Column(db.Text)
    CREATEBY = db.Column(db.Text)
    CREATEDT = db.Column(db.Text)
    MODIFYBY = db.Column(db.Text)
    MODIFYDT = db.Column(db.Text)


# =========================
# SETTINGSB
# =========================

class SettingsB(db.Model):
    __tablename__ = 'settingsb'

    id = db.Column(db.Integer, primary_key=True)

    DPATH = db.Column(db.Text)
    TPATH = db.Column(db.Text)
    LPATH = db.Column(db.Text)
    RPATH = db.Column(db.Text)
    SPATH = db.Column(db.Text)
    FPATH = db.Column(db.Text)
    PPATH = db.Column(db.Text)
    OPATH = db.Column(db.Text)
    VPATH = db.Column(db.Text)
    BPATH = db.Column(db.Text)
    SC2MSPROC = db.Column(db.Text)
    COURTID = db.Column(db.Integer)
    MODIDT = db.Column(db.Text)
    MODIBY = db.Column(db.Text)

class SettingsCTMS(db.Model):
    __tablename__ = 'settingsctms'

    id = db.Column(db.Integer, primary_key=True)

    COURTID = db.Column(db.Integer)
    CRTTYPE = db.Column(db.Text)
    JNAME = db.Column(db.Text)
    JPDESCRP = db.Column(db.Text)
    BNAME = db.Column(db.Text)
    BPDESCRP = db.Column(db.Text)
    EMAIL = db.Column(db.Text)
    TELNO = db.Column(db.Text)
    ADDRESS = db.Column(db.Text)
    ISSINGLE = db.Column(db.Integer)
    MODIDT = db.Column(db.Text)
    MODIBY = db.Column(db.Text)