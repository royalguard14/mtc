import os
import json
from app import create_app, db
from app.models import Role, User, Module, Setting, Region, Province, Municipality, Barangay
from werkzeug.security import generate_password_hash

app = create_app()

def seed_roles():
    dev = Role.query.filter_by(role_name='Developer').first()
    if not dev:
        dev = Role(id=1, role_name='Developer', modules=[1, 2, 3, 4])
        db.session.add(dev)
        db.session.commit()
        print("✅ Role: Developer created.")
    else:
        print("✔️ Role: Developer already exists.")
    return dev

def seed_user(dev_role):
    user = User.query.filter_by(username='zear').first()
    if not user:
        hashed_pw = generate_password_hash('password')
        user = User(
            id=1,
            username='zear',
            email='zear@developer.com',
            password=hashed_pw,
            role_id=dev_role.id
        )
        db.session.add(user)
        db.session.commit()
        print("✅ User: zear created.")
    else:
        print("✔️ User: zear already exists.")

def seed_modules():
    modules = [
        {'id': 1,'name': 'Roles', 'icon': 'fa-users', 'description': 'Manage roles within the system and assign permissions to users.', 'url': 'roles'},
        {'id': 2,'name': 'Users', 'icon': 'fa-users', 'description': 'Manage individual users, their details, and roles within the system.', 'url': 'users'},
        {'id': 3,'name': 'Modules', 'icon': 'fa-cogs', 'description': 'Configure and manage system modules and their settings.', 'url': 'modules'},
        {'id': 4,'name': 'Settings', 'icon': 'fa-cogs', 'description': 'Manage global system settings, including configurations and preferences.', 'url': 'settings'},
    ]
    for m in modules:
        exists = Module.query.filter_by(name=m['name']).first()
        if not exists:
            db.session.add(Module(**m))
            print(f"✅ Module: {m['name']} added.")
        else:
            print(f"✔️ Module: {m['name']} already exists.")
    db.session.commit()

def seed_settings():
    settings = [
        {'id': 1, 'function_desc': 'System Title', 'function': 'ZDS', 'type': 'frontend'},
        {'id': 2, 'function_desc': 'Maintenance Mode', 'function': '0', 'type': 'frontend'},
        {'id': 3, 'function_desc': 'Allow User Registration', 'function': '0', 'type': 'backend'},
        {'id': 4, 'function_desc': 'Admin Email Notifications', 'function': '1', 'type': 'backend'},
        {'id': 5, 'function_desc': 'API Access', 'function': '0', 'type': 'backend'},
        {'id': 6, 'function_desc': 'Email', 'function': 'zear.com', 'type': 'backend'},
        {'id': 7, 'function_desc': 'Landing', 'function': '0', 'type': 'frontend'},
    ]
    for s in settings:
        exists = Setting.query.filter_by(function_desc=s['function_desc']).first()
        if not exists:
            db.session.add(Setting(**s))
            print(f"✅ Setting: {s['function_desc']} added.")
        else:
            print(f"✔️ Setting: {s['function_desc']} already exists.")
    db.session.commit()

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def seed_addresses():
    print("⏳ Seeding address data...")

    db.session.query(Barangay).delete()
    db.session.query(Municipality).delete()
    db.session.query(Province).delete()
    db.session.query(Region).delete()
    db.session.commit()

    base_path = os.path.join(os.getcwd(), 'app', 'data')
    regions = load_json(os.path.join(base_path, 'table_region.json'))
    provinces = load_json(os.path.join(base_path, 'table_province.json'))
    municipalities = load_json(os.path.join(base_path, 'table_municipality.json'))
    barangays = load_json(os.path.join(base_path, 'table_barangay.json'))

    for r in regions:
        if r.get('region_id') and r.get('region_name') and r.get('region_description'):
            db.session.add(Region(
                region_id=r['region_id'],
                region_name=r['region_name'],
                region_description=r['region_description']
            ))
    db.session.commit()

    for p in provinces:
        if p.get('province_id') and p.get('region_id') and p.get('province_name'):
            db.session.add(Province(
                province_id=p['province_id'],
                region_id=p['region_id'],
                province_name=p['province_name']
            ))
    db.session.commit()

    for m in municipalities:
        if m.get('municipality_id') and m.get('province_id') and m.get('municipality_name'):
            db.session.add(Municipality(
                municipality_id=m['municipality_id'],
                province_id=m['province_id'],
                municipality_name=m['municipality_name']
            ))
    db.session.commit()

    for b in barangays:
        if b.get('barangay_id') and b.get('municipality_id') and b.get('barangay_name'):
            db.session.add(Barangay(
                barangay_id=b['barangay_id'],
                municipality_id=b['municipality_id'],
                barangay_name=b['barangay_name']
            ))
    db.session.commit()

    print("✔️ Address data seeded successfully.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        role = seed_roles()
        seed_user(role)
        seed_modules()
        seed_settings()
        seed_addresses()
