from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory
from models import User, Agent
from database import db, bcrypt
import os
import re

agent_bp = Blueprint("agent_bp", __name__)

# ── CONSTANTS ─────────────────────────────

VALID_GENDERS = ["male", "female", "other"]

VALID_STATES = [
    "karnataka", "tamil nadu", "kerala",
    "andhra pradesh", "telangana", "maharashtra"
]

# ── HELPERS ─────────────────────────────

def normalize_phone(phone):
    phone = str(phone) if phone else ""
    return ''.join(filter(str.isdigit, phone))[-10:] if phone else ""

# ── VALIDATIONS ─────────────────────────

def valid_name(name):
    return re.match(r"^[A-Za-z ]{2,25}$", name)

def valid_phone(phone):
    return re.match(r"^[6-9]\d{9}$", phone)

def valid_email(email):
    return not email or (len(email) <= 30 and re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def valid_age(age):
    try:
        return 18 <= int(age) <= 60
    except:
        return False

def valid_height(height):
    return not height or re.match(r"^\d{2,3}$", height)

def valid_city(city):
    return not city or re.match(r"^[A-Za-z ]{2,25}$", city)

def valid_state(state):
    return not state or state.lower() in VALID_STATES

def valid_gender(gender):
    return not gender or gender.lower() in VALID_GENDERS

def valid_birth_place(bp):
    return bp and re.match(r"^[A-Za-z ]{2,30}$", bp)

def valid_birth_time(bt):
    return bt and len(bt) >= 3


# ── LOGIN (old standalone page — kept for backward compat) ────────────────────

@agent_bp.route("/agent-login", methods=["GET", "POST"])
def agent_login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("agent_login.html", error="Enter email and password")
        if len(email) > 30:
            return render_template("agent_login.html", error="Email must be max 30 characters")
        if len(password) > 15:
            return render_template("agent_login.html", error="Password must be max 15 characters")

        agent = Agent.query.filter_by(email=email).first()

        if not agent:
            return render_template("agent_login.html", error="Agent not found")
        if not bcrypt.check_password_hash(agent.password_hash, password):
            return render_template("agent_login.html", error="Wrong password")
        if not agent.is_active:
            return render_template("agent_login.html", error="Your account has been deactivated. Contact admin.")

        session["agent_id"]   = agent.id
        session["agent_name"] = agent.name
        session["role"]       = "agent"

        return redirect(url_for("agent_bp.agent_dashboard"))

    return render_template("agent_login.html")


# ── LOGIN PORTAL (used by login.html — errors return to same page) ────────────

@agent_bp.route("/agent-login-portal", methods=["POST"])
def agent_login_portal():
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("login.html",
                               error="Enter email and password",
                               active_role="agent",
                               agent_email=email)

    if len(email) > 30:
        return render_template("login.html",
                               error="Email must be max 30 characters",
                               active_role="agent",
                               agent_email=email)

    if len(password) > 15:
        return render_template("login.html",
                               error="Password must be max 15 characters",
                               active_role="agent",
                               agent_email=email)

    agent = Agent.query.filter_by(email=email).first()

    if not agent:
        return render_template("login.html",
                               error="Agent not found",
                               active_role="agent",
                               agent_email=email)

    if not bcrypt.check_password_hash(agent.password_hash, password):
        return render_template("login.html",
                               error="Wrong password",
                               active_role="agent",
                               agent_email=email)

    if not agent.is_active:
        return render_template("login.html",
                               error="Your account has been deactivated. Contact admin.",
                               active_role="agent",
                               agent_email=email)

    session["agent_id"]   = agent.id
    session["agent_name"] = agent.name
    session["role"]       = "agent"

    return redirect(url_for("agent_bp.agent_dashboard"))


# ── DASHBOARD ─────────────────────────

@agent_bp.route("/agent-dashboard")
def agent_dashboard():
    if session.get("role") != "agent":
        return redirect(url_for("agent_bp.agent_login"))

    agent = Agent.query.get(session.get("agent_id"))

    if not agent:
        return redirect(url_for("agent_bp.agent_login"))

    users = User.query.filter_by(agent_id=agent.id).all()

    return render_template("agent_dashboard.html", agent=agent, users=users)


# ── ADD USER ─────────────────────────────

@agent_bp.route("/agent-add-user", methods=["GET", "POST"])
def agent_add_user():
    if session.get("role") != "agent":
        return redirect(url_for("agent_bp.agent_login"))

    agent = Agent.query.get(session.get("agent_id"))

    if not agent:
        return redirect(url_for("agent_bp.agent_login"))

    if request.method == "POST":

        name        = request.form.get("name", "").strip()
        phone       = normalize_phone(request.form.get("phone", ""))
        email       = request.form.get("email", "").strip()
        age         = request.form.get("age")
        gender      = request.form.get("gender", "").strip().lower()
        height      = request.form.get("height", "").strip()
        city        = request.form.get("city", "").strip()
        state       = request.form.get("state", "").strip().lower()
        birth_place = request.form.get("birth_place", "").strip()
        birth_time  = request.form.get("birth_time", "").strip()
        user_type   = request.form.get("user_type", "personal")

        errors = []

        if not name or not valid_name(name):
            errors.append("Invalid name")
        if not phone or not valid_phone(phone):
            errors.append("Invalid phone")
        if not valid_email(email):
            errors.append("Invalid email")
        if age and not valid_age(age):
            errors.append("Invalid age")
        if not valid_height(height):
            errors.append("Invalid height")
        if not valid_gender(gender):
            errors.append("Invalid gender")
        if not valid_city(city):
            errors.append("Invalid city")
        if not valid_state(state):
            errors.append("Invalid state")
        if not valid_birth_place(birth_place):
            errors.append("Invalid birth place")
        if not valid_birth_time(birth_time):
            errors.append("Invalid birth time")
        if User.query.filter_by(phone=phone).first():
            errors.append("Phone already exists")

        if errors:
            return render_template("register.html", error=", ".join(errors))

        new_user = User(
            name=name,
            phone=phone,
            email=email or None,
            age=int(age) if age else None,
            gender=gender,
            height=height,
            city=city,
            state=state,
            location=f"{city}, {state}".strip(", "),
            birth_place=birth_place,
            birth_time=birth_time,
            user_type=user_type,
            agent_id=agent.id
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("agent_bp.agent_dashboard"))

    return render_template("register.html")


# ── BULK UPLOAD ───────────────────────────

@agent_bp.route("/agent-bulk-upload", methods=["GET", "POST"])
def agent_bulk_upload():
    if session.get("role") != "agent":
        return redirect(url_for("agent_bp.agent_login"))

    agent = Agent.query.get(session.get("agent_id"))

    if not agent:
        return redirect(url_for("agent_bp.agent_login"))

    if request.method == "POST":
        file = request.files.get("excel_file")

        if not file:
            return render_template("bulk_upload.html", agent=agent, error="Select file")

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            success = 0
            skip    = 0

            for row in ws.iter_rows(min_row=2, values_only=True):
                name  = str(row[0] or "").strip()
                phone = normalize_phone(str(row[1] or ""))

                if not valid_name(name) or not valid_phone(phone):
                    skip += 1
                    continue

                if User.query.filter_by(phone=phone).first():
                    skip += 1
                    continue

                new_user = User(name=name, phone=phone, agent_id=agent.id)
                db.session.add(new_user)
                success += 1

            db.session.commit()

            return render_template(
                "bulk_upload.html", agent=agent,
                success=True, success_count=success, skip_count=skip
            )

        except Exception as e:
            return render_template("bulk_upload.html", agent=agent, error=str(e))

    return render_template("bulk_upload.html", agent=agent)


# ── DOWNLOAD TEMPLATE ─────────────────────

@agent_bp.route("/download-template")
def download_template():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    return send_from_directory(static_dir, "mangal_vows_upload_template.xlsx", as_attachment=True)


# ── LOGOUT ───────────────────────────────

@agent_bp.route("/agent-logout")
def agent_logout():
    session.clear()
    return redirect(url_for("user.home"))