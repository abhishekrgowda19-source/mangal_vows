from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User
from database import db
from datetime import datetime

user = Blueprint("user", __name__)


def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))[-10:] if phone else ""


def get_name3(name):
    return name[:3].upper() if len(name) >= 3 else name.upper()


def is_subscription_valid(user_data):
    if not user_data.subscription_active:
        return False
    if user_data.subscription_expiry and user_data.subscription_expiry < datetime.utcnow():
        return False
    return True


def subscription_redirect(user_data):
    if not user_data.subscription_expiry:
        return redirect(url_for("subscription.subscribe"))
    else:
        return redirect(url_for("subscription.renew"))


@user.route("/")
def home():
    return render_template("login.html")


# ── Commercial Login ──────────────────────────────────

@user.route("/login", methods=["POST"])
def login():
    name3 = request.form.get("name3", "").strip().upper()
    phone = normalize_phone(request.form.get("phone"))

    user_data = User.query.filter_by(phone=phone).first()

    if not user_data or get_name3(user_data.name) != name3:
        return render_template("login.html", error="Invalid credentials")

    session["user"] = user_data.phone
    session["role"] = "user"

    if not is_subscription_valid(user_data):
        return subscription_redirect(user_data)

    return redirect(url_for("user.dashboard"))


# ── Personal Login ────────────────────────────────────

@user.route("/personal-login", methods=["POST"])
def personal_login():
    name  = request.form.get("name", "").strip()
    phone = normalize_phone(request.form.get("phone"))

    user_data = User.query.filter_by(phone=phone).first()

    if not user_data or user_data.name.strip().lower() != name.lower():
        return render_template("login.html", error="Invalid credentials")

    session["user"] = user_data.phone
    session["role"] = "user"

    if not is_subscription_valid(user_data):
        return subscription_redirect(user_data)

    return redirect(url_for("user.dashboard"))


# ── Self Registration (New User) ──────────────────────

@user.route("/self-register", methods=["GET", "POST"])
def self_register():
    if request.method == "POST":
        name          = request.form.get("name", "").strip()
        phone         = normalize_phone(request.form.get("phone", ""))
        email         = request.form.get("email", "").strip()
        age           = request.form.get("age")
        gender        = request.form.get("gender", "").strip()
        height        = request.form.get("height", "").strip()
        religion      = request.form.get("religion", "").strip()
        caste         = request.form.get("caste", "").strip()
        community     = request.form.get("community", "").strip()
        mother_tongue = request.form.get("mother_tongue", "").strip()
        profession    = request.form.get("profession", "").strip()
        education     = request.form.get("education", "").strip()
        city          = request.form.get("city", "").strip()
        state         = request.form.get("state", "").strip()

        # Validation
        if not name or not phone:
            return render_template("self_register.html", error="Name and phone are required")

        if User.query.filter_by(phone=phone).first():
            return render_template("self_register.html", error="Phone already registered! Please login instead.")

        # ✅ Save new user to DB (visible in admin + agent panel)
        new_user = User(
            name          = name,
            phone         = phone,
            email         = email,
            age           = int(age) if age else None,
            gender        = gender,
            height        = height,
            religion      = religion,
            caste         = caste,
            community     = community,
            mother_tongue = mother_tongue,
            profession    = profession,
            education     = education,
            city          = city,
            state         = state,
            location      = f"{city}, {state}".strip(", "),
            agent_id      = None  # ✅ No agent — self registered
        )
        db.session.add(new_user)
        db.session.commit()

        # ✅ Auto login after registration
        session["user"] = new_user.phone
        session["role"] = "user"

        # ✅ Redirect to ₹500 payment
        return redirect(url_for("subscription.subscribe"))

    return render_template("self_register.html")


# ── Dashboard ─────────────────────────────────────────

@user.route("/dashboard")
def dashboard():
    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session.get("user")).first()
    if not user_data:
        return redirect(url_for("user.home"))

    if not is_subscription_valid(user_data):
        return subscription_redirect(user_data)

    return render_template("dashboard.html", user=user_data)


# ── Search ────────────────────────────────────────────

@user.route("/search")
def search():
    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session.get("user")).first()
    if not user_data:
        return redirect(url_for("user.home"))

    if not is_subscription_valid(user_data):
        return subscription_redirect(user_data)

    age_min       = request.args.get("age_min")
    age_max       = request.args.get("age_max")
    height        = request.args.get("height")
    location      = request.args.get("location")
    profession    = request.args.get("profession")
    community     = request.args.get("community")
    mother_tongue = request.args.get("mother_tongue")
    religion      = request.args.get("religion")
    caste         = request.args.get("caste")
    gender        = request.args.get("gender")

    query = User.query.filter(User.phone != user_data.phone)

    if age_min:
        try: query = query.filter(User.age >= int(age_min))
        except ValueError: pass
    if age_max:
        try: query = query.filter(User.age <= int(age_max))
        except ValueError: pass
    if height:
        query = query.filter(User.height.ilike(f"%{height}%"))
    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))
    if profession:
        query = query.filter(User.profession.ilike(f"%{profession}%"))
    if community:
        query = query.filter(User.community.ilike(f"%{community}%"))
    if mother_tongue:
        query = query.filter(User.mother_tongue.ilike(f"%{mother_tongue}%"))
    if religion:
        query = query.filter(User.religion.ilike(f"%{religion}%"))
    if caste:
        query = query.filter(User.caste.ilike(f"%{caste}%"))
    if gender:
        query = query.filter(User.gender == gender)

    users = query.all()
    return render_template("dashboard.html", users=users, user=user_data)


# ── Logout ────────────────────────────────────────────

@user.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.home"))
# ── Report a Profile ──────────────────────────────────

@user.route("/report/<reported_id>", methods=["GET", "POST"])
def report_profile(reported_id):
    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session.get("user")).first()
    reported  = User.query.get(reported_id)

    if not user_data or not reported:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        from models import Dispute
        dispute = Dispute(
            raised_by   = user_data.id,
            against     = reported_id,
            subject     = request.form.get("subject", "").strip(),
            description = request.form.get("description", "").strip(),
            status      = "open"
        )
        db.session.add(dispute)
        db.session.commit()
        return redirect(url_for("user.dashboard"))

    return render_template("report.html", reported=reported)