from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User
from database import db
from datetime import datetime

user = Blueprint("user", __name__)

# ----------------------------------------
# HELPERS
# ----------------------------------------

def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))[-10:] if phone else ""


def get_name3(name):
    return name[:3].upper() if len(name) >= 3 else name.upper()

# ----------------------------------------
# HOME
# ----------------------------------------

@user.route("/")
def home():
    return render_template("login.html")

# ----------------------------------------
# LOGIN
# ----------------------------------------

@user.route("/login", methods=["POST"])
def login():

    name3 = request.form.get("name3", "").upper().strip()
    phone = normalize_phone(request.form.get("phone"))

    user_data = User.query.filter_by(phone=phone).first()

    if not user_data or get_name3(user_data.name) != name3:
        return render_template("login.html", error="Invalid credentials")

    session["user"] = user_data.phone
    session["role"] = "user"

    return redirect(url_for("user.dashboard"))

# ----------------------------------------
# DASHBOARD
# ----------------------------------------

@user.route("/dashboard")
def dashboard():

    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session.get("user")).first()

    if not user_data:
        return redirect(url_for("user.home"))

    # 🔐 subscription check with expiry
    if not user_data.subscription_active or (
        user_data.subscription_expiry and user_data.subscription_expiry < datetime.utcnow()
    ):
        return render_template("subscribe.html")

    return render_template("dashboard.html", user=user_data)

# ----------------------------------------
# SEARCH
# ----------------------------------------

@user.route("/search")
def search():

    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    age = request.args.get("age")
    location = request.args.get("location")
    profession = request.args.get("profession")

    query = User.query

    if age:
        query = query.filter_by(age=int(age))

    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))

    if profession:
        query = query.filter(User.profession.ilike(f"%{profession}%"))

    users = query.all()

    return render_template("dashboard.html", users=users)

# ----------------------------------------
# LOGOUT
# ----------------------------------------

@user.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.home"))