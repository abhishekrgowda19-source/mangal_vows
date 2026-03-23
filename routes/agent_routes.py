from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Agent
from database import db

agent_bp = Blueprint("agent_bp", __name__)


def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))[-10:] if phone else ""


@agent_bp.route("/agent-login", methods=["GET", "POST"])
def agent_login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        agent = Agent.query.filter_by(email=email).first()

        from app import bcrypt
        if not agent or not bcrypt.check_password_hash(agent.password_hash, password):
            return render_template("login.html", error="Invalid agent credentials")

        session["agent"] = agent.id
        session["role"]  = "agent"
        return redirect(url_for("agent_bp.agent_dashboard"))

    return render_template("login.html")


@agent_bp.route("/agent-dashboard")
def agent_dashboard():
    if session.get("role") != "agent":
        return redirect(url_for("agent_bp.agent_login"))

    agent = Agent.query.get(session.get("agent"))
    if not agent:
        return redirect(url_for("agent_bp.agent_login"))

    users = User.query.filter_by(agent_id=agent.id).all()
    return render_template("agent_dashboard.html", agent=agent, users=users)


@agent_bp.route("/agent-add-user", methods=["GET", "POST"])
def agent_add_user():
    if session.get("role") != "agent":
        return redirect(url_for("agent_bp.agent_login"))

    agent = Agent.query.get(session.get("agent"))

    if request.method == "POST":
        name          = request.form.get("name", "").strip()
        phone         = normalize_phone(request.form.get("phone", ""))
        email         = request.form.get("email", "").strip()
        age           = request.form.get("age")
        gender        = request.form.get("gender", "").strip()
        height        = request.form.get("height", "").strip()
        profession    = request.form.get("profession", "").strip()
        education     = request.form.get("education", "").strip()
        city          = request.form.get("city", "").strip()
        state         = request.form.get("state", "").strip()
        religion      = request.form.get("religion", "").strip()
        caste         = request.form.get("caste", "").strip()  # ✅ caste
        community     = request.form.get("community", "").strip()
        mother_tongue = request.form.get("mother_tongue", "").strip()

        if not name or not phone:
            return render_template("register.html", error="Name and phone are required")

        if User.query.filter_by(phone=phone).first():
            return render_template("register.html", error="Phone already registered")

        new_user = User(
            name          = name,
            phone         = phone,
            email         = email,
            age           = int(age) if age else None,
            gender        = gender,
            height        = height,
            profession    = profession,
            education     = education,
            city          = city,
            state         = state,
            location      = f"{city}, {state}".strip(", "),
            religion      = religion,
            caste         = caste,  # ✅ caste
            community     = community,
            mother_tongue = mother_tongue,
            agent_id      = agent.id
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("agent_bp.agent_dashboard"))

    return render_template("register.html")


@agent_bp.route("/agent-logout")
def agent_logout():
    session.clear()
    return redirect(url_for("user.home"))