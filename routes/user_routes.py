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
        return redirect(url_for("subscription.subscribe"))

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
        return redirect(url_for("subscription.subscribe"))

    return redirect(url_for("user.dashboard"))


# ── Dashboard ─────────────────────────────────────────

@user.route("/dashboard")
def dashboard():
    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session.get("user")).first()
    if not user_data:
        return redirect(url_for("user.home"))

    if not is_subscription_valid(user_data):
        return redirect(url_for("subscription.subscribe"))

    return render_template("dashboard.html", user=user_data)


# ── Search ────────────────────────────────────────────

@user.route("/search")
def search():
    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session.get("user")).first()
    if not user_data or not is_subscription_valid(user_data):
        return redirect(url_for("subscription.subscribe"))

    age        = request.args.get("age")
    location   = request.args.get("location")
    profession = request.args.get("profession")

    query = User.query

    if age:
        try:
            query = query.filter_by(age=int(age))
        except ValueError:
            pass

    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))

    if profession:
        query = query.filter(User.profession.ilike(f"%{profession}%"))

    users = query.all()
    return render_template("dashboard.html", users=users)


# ── Logout ────────────────────────────────────────────

@user.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.home"))