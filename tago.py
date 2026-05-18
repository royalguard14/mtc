

SCHEDULE_MASTER_API_URL_BASE = (
    "https://script.google.com/macros/s/AKfycbw2My5Z1KySGX-7WwFb9i-JMh7l6e7oDX-xdmbHzrEgOGpEQ1kSALIgal6zmP5kLFBW/exec"
)


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    # --------------------------
    # ISO FORMAT (your current issue)
    # --------------------------
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "")).date()
    except:
        pass

    # --------------------------
    # FALLBACK FORMATS
    # --------------------------
    formats = [
        "%m-%d-%y",
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def safe_str(value):
    """Prevent crash on int/None values"""
    return str(value).strip() if value is not None else ""


@schedule_bp.route('/api/import-cases/<case_type>')
def import_cases(case_type):
    try:
        sheet_map = {
            "civil": "civil",
            "criminal": "criminal",
            "smallclaims": "smallcase"
        }

        if case_type not in sheet_map:
            return jsonify({"status": "error", "message": "Invalid case type"}), 400

        url = f"{SCHEDULE_MASTER_API_URL_BASE}?api={sheet_map[case_type]}"

        response = requests.get(url, timeout=60)
        response.raise_for_status()
        records = response.json()

        # db.session.query(Cases).delete()
        # db.session.commit()

        count = 0
        skipped = 0

        for row in records:

            # -------------------------
            # SAFE EXTRACTION
            # -------------------------
            case_number = safe_str(row.get('caseNum') or row.get('CASENUM'))
            title = safe_str(row.get('caseTitle') or row.get('TITLE'))
            nature = safe_str(row.get('NATURE'))
            action_value = safe_str(row.get('action') or row.get('ACTION')).upper()
            date_value = row.get('dtRecieved') or row.get('DATE FILED')

            if not case_number or not title:
                skipped += 1
                continue

            # -------------------------
            # FILTER LOGIC PER CASE TYPE
            # -------------------------

            if case_type == "civil":
                if action_value != "COMPLAINT":
                    continue

            elif case_type == "smallclaims":
                if action_value != "STATEMENTS OF CLAIMS":
                    continue

            # criminal = no filter (or you can add later)

            # -------------------------
            # CREATE RECORD
            # -------------------------
            record = Cases(
                case_number=case_number,
                title=title,
                nature=nature or None,
                date_filed=parse_date(date_value),
                case_type=case_type.upper(),
                action={},
                information={},
                filepath=None
            )

            db.session.add(record)
            count += 1

        db.session.commit()

        return jsonify({
            "status": "success",
            "type": case_type,
            "imported": count,
            "skipped": skipped,
            "total_rows": len(records)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500