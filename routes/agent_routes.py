from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Agent
from database import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
agent_bp = Blueprint("agent_bp", __name__)


@agent_bp.route("/agent-login", methods=["GET", "POST"])
def agent_login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        agent = Agent.query.filter_by(email=email).first()

        if not agent or not bcrypt.check_password_hash(agent.password_hash, password):
            return render_template("agent_login.html", error="Invalid credentials")

        session["agent"] = agent.id
        session["role"]  = "agent"
        return redirect(url_for("agent_bp.agent_dashboard"))

    return render_template("agent_login.html")


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
        name  = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not phone:
            return render_template("register.html", error="Name and phone are required")

        existing = User.query.filter_by(phone=phone).first()
        if existing:
            return render_template("register.html", error="Phone already registered")

        new_user = User(
            name     = name,
            phone    = phone,
            agent_id = agent.id
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("agent_bp.agent_dashboard"))

    return render_template("register.html")


@agent_bp.route("/agent-logout")
def agent_logout():
    session.clear()
    return redirect(url_for("agent_bp.agent_login"))