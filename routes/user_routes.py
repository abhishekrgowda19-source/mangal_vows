from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User
from database import db
import re

user = Blueprint("user", __name__)


def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone or ""))[-10:]


def is_valid_phone(phone):
    return re.fullmatch(r"[6-9]\d{9}", phone)


def is_valid_name(name):
    return re.fullmatch(r"[A-Za-z ]{2,50}", name)


def is_valid_commercial_name(name):
    return re.fullmatch(r"[A-Za-z ]{2,10}", name)


def normalize_birth_time(raw):
    if not raw:
        return None
    raw = raw.strip().upper()
    match = re.fullmatch(r"(1[0-2]|0?[1-9]):([0-5][0-9])\s*(AM|PM)", raw)
    if not match:
        return None
    hour   = int(match.group(1))
    minute = match.group(2)
    period = match.group(3)
    return f"{hour}:{minute} {period}"


def is_valid_birth_place(place):
    return place and re.fullmatch(r"[A-Za-z ,\.]{2,100}", place)


# ── AI SMART MATCH SCORING ──────────────────────────────
def calculate_match_score(u, gender, age_min, age_max, community,
                           mother_tongue, profession, city, religion):
    score = 0
    total = 0

    if gender:
        total += 20
        if u.get("gender", "").lower() == gender.lower():
            score += 20

    if age_min or age_max:
        total += 20
        age = u.get("age") or 0
        min_ok = (int(age_min) <= age) if age_min else True
        max_ok = (age <= int(age_max)) if age_max else True
        if min_ok and max_ok:
            score += 20
        elif min_ok or max_ok:
            score += 10  # partial age match

    if religion:
        total += 15
        if religion.lower() in (u.get("religion") or "").lower():
            score += 15

    if community:
        total += 15
        if community.lower() in (u.get("community") or "").lower():
            score += 15

    if mother_tongue:
        total += 10
        if mother_tongue.lower() in (u.get("mother_tongue") or "").lower():
            score += 10

    if city:
        total += 10
        if city.lower() in (u.get("city") or "").lower():
            score += 10

    if profession:
        total += 10
        if profession.lower() in (u.get("profession") or "").lower():
            score += 10

    if total == 0:
        return 100  # no filters = show all at 100%

    return round((score / total) * 100)


# ---------------- HOME ----------------
@user.route("/")
def home():
    return redirect(url_for("user.login"))


# ---------------- LOGIN ----------------
@user.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        session.clear()

    if request.method == "POST":

        phone    = normalize_phone(request.form.get("phone", ""))
        login_as = request.form.get("login_as", "").strip()

        if not phone or not is_valid_phone(phone):
            return render_template("login.html", error="Invalid phone number")

        user_data = User.query.filter_by(phone=phone).first()

        # ---------------- COMMERCIAL LOGIN ----------------
        if login_as == "commercial":

            if user_data:
                session["user_id"]    = user_data.id
                session["role"]       = "user"
                session["user_type"]  = user_data.user_type
                session["user_name"]  = user_data.name
                session["user_phone"] = user_data.phone
                session["user_email"] = user_data.email or ""

                return redirect(url_for("user.dashboard"))

            return render_template("login.html")

        # ---------------- PERSONAL LOGIN ----------------
        if login_as == "personal":

            if not user_data:
                return render_template(
                    "login.html",
                    error="Phone not registered. Please register as Personal user."
                )

            if user_data.user_type != "personal":
                session["user_id"]    = user_data.id
                session["role"]       = "user"
                session["user_type"]  = user_data.user_type
                session["user_name"]  = user_data.name
                session["user_phone"] = user_data.phone
                session["user_email"] = user_data.email or ""
                return redirect(url_for("user.dashboard"))

            name        = request.form.get("name", "").strip()
            birth_time  = request.form.get("birth_time", "").strip()
            birth_place = request.form.get("birth_place", "").strip()

            normalized_input = normalize_birth_time(birth_time)

            if normalized_input is None:
                return render_template(
                    "login.html",
                    error="Invalid birth time format. Use format like 5:30 AM"
                )

            if (
                name.lower()                != (user_data.name or "").lower() or
                normalized_input            != (user_data.birth_time or "") or
                birth_place.lower().strip() != (user_data.birth_place or "").lower().strip()
            ):
                return render_template("login.html", error="Invalid credentials")

            session["user_id"]    = user_data.id
            session["role"]       = "user"
            session["user_type"]  = user_data.user_type
            session["user_name"]  = user_data.name
            session["user_phone"] = user_data.phone
            session["user_email"] = user_data.email or ""

            if not user_data.subscription_active:
                if user_data.needs_renewal():
                    return redirect(url_for("subscription.renew"))
                return redirect(url_for("subscription.subscribe"))

            return redirect(url_for("user.dashboard"))

    return render_template("login.html")


# ---------------- PERSONAL REGISTER ----------------
@user.route("/self-register", methods=["GET", "POST"])
def self_register():

    if request.method == "POST":

        name        = request.form.get("name", "").strip()
        phone       = normalize_phone(request.form.get("phone", ""))
        email       = request.form.get("email", "").strip() or None
        age         = request.form.get("age")
        gender      = request.form.get("gender", "")
        city        = request.form.get("city", "").strip()
        state       = request.form.get("state", "").strip()
        birth_place = request.form.get("birth_place", "").strip()
        birth_time  = request.form.get("birth_time", "").strip()

        if not is_valid_phone(phone):
            return render_template("self_register.html", error="Invalid phone number")

        if not is_valid_name(name):
            return render_template("self_register.html", error="Name must be 2-50 letters only")

        normalized_time = normalize_birth_time(birth_time)
        if not normalized_time:
            return render_template(
                "self_register.html",
                error="Invalid birth time. Use format like 5:30 AM or 11:45 PM"
            )

        if not is_valid_birth_place(birth_place):
            return render_template(
                "self_register.html",
                error="Invalid birth place. Only letters, spaces, commas allowed"
            )

        if not age or not age.isdigit() or not (18 <= int(age) <= 80):
            return render_template("self_register.html", error="Age must be between 18 and 80")

        if User.query.filter_by(phone=phone).first():
            return render_template("self_register.html", error="User already exists")

        new_user = User(
            name=name,
            phone=phone,
            email=email,
            age=int(age),
            gender=gender,
            city=city,
            state=state,
            location=f"{city}, {state}",
            birth_place=birth_place,
            birth_time=normalized_time,
            user_type="personal",
            subscription_active=False
        )

        db.session.add(new_user)
        db.session.commit()

        session.clear()
        session["user_id"]    = new_user.id
        session["role"]       = "user"
        session["user_type"]  = "personal"
        session["user_name"]  = new_user.name
        session["user_phone"] = new_user.phone
        session["user_email"] = new_user.email or ""

        return redirect(url_for("subscription.subscribe"))

    return render_template("self_register.html")


# ---------------- COMMERCIAL REGISTER ----------------
@user.route("/commercial-register", methods=["POST"])
def commercial_register():

    name  = request.form.get("name", "").strip()
    phone = normalize_phone(request.form.get("phone", ""))

    if not name or not is_valid_commercial_name(name):
        return render_template(
            "login.html",
            error="Name must be 2–10 letters only for commercial login"
        )

    if not is_valid_phone(phone):
        return render_template("login.html", error="Invalid phone number")

    existing = User.query.filter_by(phone=phone).first()

    if existing:
        if existing.user_type == "commercial":
            if existing.name != name:
                existing.name = name
                db.session.commit()

            session["user_id"]    = existing.id
            session["role"]       = "user"
            session["user_type"]  = "commercial"
            session["user_name"]  = existing.name
            session["user_phone"] = existing.phone
            session["user_email"] = existing.email or ""

            return redirect(url_for("user.dashboard"))

        return render_template(
            "login.html",
            error="This phone is already registered as a Personal user."
        )

    try:
        new_user = User(
            name=name,
            phone=phone,
            email=None,
            user_type="commercial",
            subscription_active=False
        )

        db.session.add(new_user)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] commercial_register failed: {e}")
        return render_template(
            "login.html",
            error="Registration failed. Please try again."
        )

    session.clear()
    session["user_id"]    = new_user.id
    session["role"]       = "user"
    session["user_type"]  = "commercial"
    session["user_name"]  = new_user.name
    session["user_phone"] = new_user.phone
    session["user_email"] = ""

    return redirect(url_for("user.dashboard"))


# ---------------- DASHBOARD ----------------
@user.route("/dashboard")
def dashboard():

    if session.get("role") != "user":
        return redirect(url_for("user.login"))

    user_data = User.query.get(session["user_id"])

    if not user_data:
        session.clear()
        return redirect(url_for("user.login"))

    session["user_type"] = user_data.user_type

    if user_data.user_type == "personal" and not user_data.subscription_active:
        if user_data.needs_renewal():
            return redirect(url_for("subscription.renew"))
        return redirect(url_for("subscription.subscribe"))

    viewer_type = user_data.user_type
    viewer_sub  = user_data.subscription_active

    search        = request.args.get("search", "").strip()
    gender        = request.args.get("gender", "").strip()
    age_min       = request.args.get("age_min", "").strip()
    age_max       = request.args.get("age_max", "").strip()
    community     = request.args.get("community", "").strip()
    mother_tongue = request.args.get("mother_tongue", "").strip()
    profession    = request.args.get("profession", "").strip()
    city          = request.args.get("city", "").strip()
    religion      = request.args.get("religion", "").strip()

    # ── Check if any filter is applied ──
    filters_applied = any([gender, age_min, age_max, community,
                            mother_tongue, profession, city, religion])

    query = User.query.filter(User.id != user_data.id)

    # ── Name search is always exact filter ──
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))

    users = query.all()

    safe_users = []
    for u in users:
        u_dict = u.to_dict(
            viewer_subscription_active=viewer_sub,
            viewer_type=viewer_type
        )

        # ── Add AI match score ──
        if filters_applied:
            u_dict["match_score"] = calculate_match_score(
                u_dict, gender, age_min, age_max,
                community, mother_tongue, profession, city, religion
            )
        else:
            u_dict["match_score"] = None

        safe_users.append(u_dict)

    # ── Sort by match score if filters applied ──
    if filters_applied:
        safe_users = sorted(safe_users, key=lambda x: x["match_score"], reverse=True)
        # ── Only show profiles with at least 30% match ──
        safe_users = [u for u in safe_users if u["match_score"] >= 30]

    return render_template(
        "dashboard.html",
        users=safe_users,
        user=user_data,
        viewer_type=viewer_type,
        subscription_active=viewer_sub,
        filters_applied=filters_applied
    )


# ---------------- LOGOUT ----------------
@user.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.login"))