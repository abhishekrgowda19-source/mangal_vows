from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Agent, Admin
from database import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin = Admin.query.filter_by(username=username).first()

        if not admin or not bcrypt.check_password_hash(admin.password_hash, password):
            return render_template("login.html", error="Invalid admin credentials")

        session["admin"] = admin.username
        session["role"]  = "admin"
        return redirect(url_for("admin_bp.admin_dashboard"))

    return render_template("login.html")


@admin_bp.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("admin_bp.admin_login"))

    users  = User.query.count()
    agents = Agent.query.count()

    return render_template("admin_dashboard.html", users=users, agents=agents)


@admin_bp.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("user.home"))