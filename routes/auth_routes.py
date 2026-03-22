from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User
from database import db

auth = Blueprint("auth", __name__)

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

@auth.route("/", methods=["GET"])
def home():
    return render_template("login.html")


# ----------------------------------------
# LOGIN (FIXED)
# ----------------------------------------

@auth.route("/login", methods=["POST"])
def login():

    name3 = request.form.get("name3", "").strip().upper()
    phone = normalize_phone(request.form.get("phone"))

    user = User.query.filter_by(phone=phone).first()

    if not user or get_name3(user.name) != name3:
        return render_template("login.html", error="Invalid credentials")

    session["user"] = user.phone
    session["role"] = "user"

    # 🔐 Subscription check (with expiry safety)
    if not user.subscription_active:
        return render_template("subscribe.html")

    return redirect(url_for("dashboard"))