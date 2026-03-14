from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User
from database import db

auth = Blueprint("auth", __name__)

def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))[-10:]


@auth.route("/", methods=["GET"])
def home():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login():

    name3 = request.form["name3"].strip().upper()
    birthtime = request.form["birthtime"]
    birthplace = request.form["birthplace"].strip().lower()
    phone = normalize_phone(request.form["phone"])

    user = User.query.filter_by(
        name3=name3,
        birthtime=birthtime,
        birthplace=birthplace,
        phone=phone
    ).first()

    if user:

        session["user"] = user.phone

        if user.subscription_active:
            return redirect(url_for("dashboard"))

        return redirect(url_for("subscribe"))

    return "Invalid credentials"