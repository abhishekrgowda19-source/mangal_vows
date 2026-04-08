from flask import Blueprint, request, jsonify, session
from models import User
from database import db
import re

api_bp = Blueprint("api", __name__, url_prefix="/api")

def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone or ""))[-10:]

def is_valid_phone(phone):
    return re.fullmatch(r"[6-9]\d{9}", phone)

def normalize_birth_time(raw):
    if not raw:
        return None
    raw = raw.strip().upper()
    match = re.fullmatch(r"(1[0-2]|0?[1-9]):([0-5][0-9])\s*(AM|PM)", raw)
    if not match:
        return None
    hour = int(match.group(1))
    minute = match.group(2)
    period = match.group(3)
    return f"{hour}:{minute} {period}"

# ── LOGIN API ──
@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json()
    phone = normalize_phone(data.get("phone", ""))
    login_as = data.get("login_as", "personal")

    if not is_valid_phone(phone):
        return jsonify({"status": "error", "message": "Invalid phone number"})

    user_data = User.query.filter_by(phone=phone).first()

    if login_as == "commercial":
        if not user_data:
            return jsonify({"status": "error", "message": "Phone not registered"})
        return jsonify({
            "status": "success",
            "user_id": user_data.id,
            "user_type": user_data.user_type,
            "name": user_data.name,
            "phone": user_data.phone,
            "subscription_active": user_data.subscription_active
        })

    if login_as == "personal":
        if not user_data:
            return jsonify({"status": "error", "message": "Phone not registered"})

        name = data.get("name", "").strip()
        birth_time = data.get("birth_time", "").strip()
        birth_place = data.get("birth_place", "").strip()
        normalized_input = normalize_birth_time(birth_time)

        if not normalized_input:
            return jsonify({"status": "error", "message": "Invalid birth time. Use format like 5:30 AM"})

        if (
            name.lower() != (user_data.name or "").lower() or
            normalized_input != (user_data.birth_time or "") or
            birth_place.lower().strip() != (user_data.birth_place or "").lower().strip()
        ):
            return jsonify({"status": "error", "message": "Invalid credentials"})

        return jsonify({
            "status": "success",
            "user_id": user_data.id,
            "user_type": user_data.user_type,
            "name": user_data.name,
            "phone": user_data.phone,
            "subscription_active": user_data.subscription_active
        })

    return jsonify({"status": "error", "message": "Invalid login type"})


# ── REGISTER API ──
@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json()
    name = data.get("name", "").strip()
    phone = normalize_phone(data.get("phone", ""))
    email = data.get("email", "").strip() or None
    age = data.get("age")
    gender = data.get("gender", "")
    city = data.get("city", "").strip()
    state = data.get("state", "").strip()
    birth_place = data.get("birth_place", "").strip()
    birth_time = data.get("birth_time", "").strip()

    if not is_valid_phone(phone):
        return jsonify({"status": "error", "message": "Invalid phone number"})

    normalized_time = normalize_birth_time(birth_time)
    if not normalized_time:
        return jsonify({"status": "error", "message": "Invalid birth time. Use format like 5:30 AM"})

    if User.query.filter_by(phone=phone).first():
        return jsonify({"status": "error", "message": "Phone already registered"})

    new_user = User(
        name=name, phone=phone, email=email,
        age=int(age), gender=gender, city=city,
        state=state, location=f"{city}, {state}",
        birth_place=birth_place, birth_time=normalized_time,
        user_type="personal", subscription_active=False
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "user_id": new_user.id,
        "message": "Registration successful"
    })


# ── DASHBOARD / SEARCH API ──
@api_bp.route("/dashboard", methods=["POST"])
def api_dashboard():
    data = request.get_json()
    user_id = data.get("user_id")
    gender = data.get("gender", "")
    age_min = data.get("age_min", "")
    age_max = data.get("age_max", "")
    religion = data.get("religion", "")
    community = data.get("community", "")
    city = data.get("city", "")

    user_data = User.query.get(user_id)
    if not user_data:
        return jsonify({"status": "error", "message": "User not found"})

    query = User.query.filter(User.id != user_id)
    users = query.all()

    safe_users = []
    for u in users:
        u_dict = u.to_dict(
            viewer_subscription_active=user_data.subscription_active,
            viewer_type=user_data.user_type
        )
        safe_users.append(u_dict)

    return jsonify({
        "status": "success",
        "profiles": safe_users,
        "user": {
            "name": user_data.name,
            "user_type": user_data.user_type,
            "subscription_active": user_data.subscription_active
        }
    })