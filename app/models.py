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
