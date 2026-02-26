from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mangal_secret_key")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "postgresql://mangal_vows_db_user:x32SdxXBh5upKZTQJemVVFbWWpFGQDSg@dpg-d6fsuo8gjchc73d3631g-a/mangal_vows_db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --------- Database Model ---------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name3 = db.Column(db.String(10))
    surname3 = db.Column(db.String(10))
    birthtime = db.Column(db.String(10))
    birthplace = db.Column(db.String(100))
    phone = db.Column(db.String(20), unique=True)
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_expiry = db.Column(db.DateTime, nullable=True)


# --------- Utility ---------

def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))[-10:]


# --------- Routes ---------

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    name3 = request.form["name3"].strip().upper()
    birthtime = request.form["birthtime"].strip()
    birthplace = request.form["birthplace"].strip().lower()
    phone = normalize_phone(request.form["phone"])

    user = User.query.filter_by(phone=phone).first()

    if user and \
       user.name3.upper() == name3 and \
       user.birthtime == birthtime and \
       user.birthplace.lower() == birthplace:

        session["user"] = user.phone

        if user.subscription_active and user.subscription_expiry and user.subscription_expiry > datetime.utcnow():
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("subscribe"))

    return "Invalid Credentials"


@app.route("/subscribe")
def subscribe():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("subscribe.html")


@app.route("/activate", methods=["POST"])
def activate():

    if "user" not in session:
        return redirect(url_for("home"))

    user = User.query.filter_by(phone=session["user"]).first()

    if user:
        user.subscription_active = True
        user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)