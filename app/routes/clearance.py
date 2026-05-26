from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify

from flask_login import login_required, current_user, login_user

from app import db
from datetime import datetime
from app.models import Certificate

from app.routes.decorators import require_module

clearance_bp = Blueprint('clearance', __name__, url_prefix='/clearance')


# ======================================================
# INDEX PAGE
# ======================================================
@clearance_bp.route('/')
@login_required
@require_module(5)
def index():

    clearances = Certificate.query.order_by(Certificate.id.desc()).all()

    return render_template(
        "clearance/index.html",
        clearances=clearances
    )


# ======================================================
# CREATE CERTIFICATE
# ======================================================
@clearance_bp.route('/create', methods=['POST'])
@login_required
def create_certificate():
    try:
        # -------------------------
        # GET COMMON FORM DATA
        # -------------------------
        full_name = request.form.get("full_name")
        cert_type = request.form.get("cert_type")

        # -------------------------
        # VALIDATION
        # -------------------------
        if not full_name or not cert_type:
            flash("Full name and certificate type are required.", "danger")
            return redirect(url_for('clearance.index'))

        # -------------------------
        # BUILD JSON INFORMATION
        # -------------------------
        if cert_type == "COURT_CLEARANCE":
            information = {
                "address": request.form.get("address"),
                "gender": request.form.get("gender"),
                "purpose": request.form.get("purpose")
            }

        elif cert_type == "LAND_TITLE_CLEARANCE":
            amount_figure = request.form.get("amount_figure", "0").replace(",", "")

            information = {
                "owner" : request.form.get("owner"),
                "land_type": request.form.get("land_type"),
                "location": request.form.get("location"),
                "tax_no": request.form.get("tax_no"),
                "property_id": request.form.get("property_id"),
                "cadastral_lot_no": request.form.get("cadastral_lot_no"),
                "total_area": request.form.get("total_area"),
                "bounded_north": request.form.get("bounded_north"),
                "bounded_south": request.form.get("bounded_south"),
                "bounded_east": request.form.get("bounded_east"),
                "bounded_west": request.form.get("bounded_west"),
                "amount_text": request.form.get("amount_text"),
                "amount_figure": amount_figure,   # ✅ FIXED HERE
                "gender": request.form.get("gender")
            }

            
        else:
            flash("Invalid certificate type.", "danger")
            return redirect(url_for('clearance.index'))

        # -------------------------
        # CREATE RECORD
        # -------------------------
        cert = Certificate(
            full_name=full_name,
            cert_type=cert_type,
            information=information,
            date_given=datetime.today().date()
        )

        db.session.add(cert)
        db.session.commit()

        flash("Certificate created successfully!", "success")
        return redirect(url_for('clearance.index'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating certificate: {str(e)}", "danger")
        return redirect(url_for('clearance.index'))

@clearance_bp.route('/view/<int:id>')
@login_required
def view_certificate(id):
    cert = Certificate.query.get_or_404(id)
    return jsonify(cert.to_dict())


@clearance_bp.route('/update', methods=['POST'])
@login_required
def update_certificate():

    cert = Certificate.query.get_or_404(request.form.get('id'))

    cert.full_name = request.form.get('full_name')
    cert.jeps = request.form.get('jeps')

    cert_type = cert.cert_type  # IMPORTANT

    # default safe dict
    info = cert.information or {}

    if cert_type == "COURT_CLEARANCE":
        cert.information = {
            "address": request.form.get("address"),
            "gender": request.form.get("gender"),
            "purpose": request.form.get("purpose")
        }

    elif cert_type == "LAND_TITLE_CLEARANCE":
        cert.information = {
            "owner" : request.form.get("owner"),
            "land_type": request.form.get("land_type"),
            "location": request.form.get("location"),
            "tax_no": request.form.get("tax_no"),
            "property_id": request.form.get("property_id"),
            "cadastral_lot_no": request.form.get("cadastral_lot_no"),
            "total_area": request.form.get("total_area"),
            "bounded_north": request.form.get("bounded_north"),
            "bounded_south": request.form.get("bounded_south"),
            "bounded_east": request.form.get("bounded_east"),
            "bounded_west": request.form.get("bounded_west"),
            "amount_text": request.form.get("amount_text"),
            "amount_figure": request.form.get("amount_figure", "0").replace(",", ""),
            "gender": request.form.get("gender")
        }

    db.session.commit()

    return jsonify({"success": True})


# ======================================================
# HELPER: NUMBER TO WORDS
# ======================================================
def number_to_words(n):
    units = [
        "", "One", "Two", "Three", "Four", "Five",
        "Six", "Seven", "Eight", "Nine", "Ten",
        "Eleven", "Twelve", "Thirteen", "Fourteen",
        "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"
    ]

    tens = [
        "", "", "Twenty", "Thirty", "Forty",
        "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    ]

    def convert_hundreds(num):
        words = ""

        if num >= 100:
            words += units[num // 100] + " Hundred"
            num %= 100
            if num:
                words += " "

        if num >= 20:
            words += tens[num // 10]
            num %= 10
            if num:
                words += " " + units[num]
        elif num > 0:
            words += units[num]

        return words

    if n == 0:
        return "Zero"

    parts = []

    billions = n // 1_000_000_000
    if billions:
        parts.append(convert_hundreds(billions) + " Billion")
        n %= 1_000_000_000

    millions = n // 1_000_000
    if millions:
        parts.append(convert_hundreds(millions) + " Million")
        n %= 1_000_000

    thousands = n // 1_000
    if thousands:
        parts.append(convert_hundreds(thousands) + " Thousand")
        n %= 1_000

    if n:
        parts.append(convert_hundreds(n))

    return " ".join(parts).strip()


def amount_to_words(amount=0):
    amount = round(float(amount or 0), 2)

    whole = int(amount)
    cents = int(round((amount - whole) * 100))

    words = number_to_words(whole).upper()

    if cents > 0:
        cents_words = number_to_words(cents).upper()
        return f"{words} and {cents_words} CENT/S"
    else:
        return f"{words} "

# ======================================================
# API: CONVERT AMOUNT TO WORDS
# ======================================================
@clearance_bp.route('/amount-to-words')
@login_required
def amount_to_words_api():
    try:
        amount = request.args.get('amount', '0').replace(',', '')
        words = amount_to_words(amount)

        return jsonify({
            "success": True,
            "amount_text": words
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "amount_text": "",
            "error": str(e)
        })


