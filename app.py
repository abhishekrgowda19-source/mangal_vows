from flask import Flask, render_template, request, redirect, url_for, session
from config import Config
from database import db
from models import User, Agent
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SECRET_KEY", "mangal_secret_key")

db.init_app(app)
bcrypt = Bcrypt(app)


# ---------------- ADMIN SECURITY ----------------

class SecureModelView(ModelView):

    def is_accessible(self):
        return session.get("role") == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin_login"))


# ---------------- ADMIN PANEL ----------------

admin = Admin(app, name="Mangal Vows Admin")
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Agent, db.session))


# ---------------- CREATE TABLES ----------------

with app.app_context():
    db.create_all()


# ---------------- UTIL FUNCTIONS ----------------

def normalize_phone(phone):
    if not phone:
        return ""
    return ''.join(filter(str.isdigit, phone))[-10:]


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("login.html")


# ---------------- REGISTER USER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        phone = normalize_phone(request.form["phone"])

        age = request.form.get("age")
        height = request.form.get("height")
        profession = request.form.get("profession")
        location = request.form.get("location")

        existing_user = User.query.filter_by(phone=phone).first()

        if existing_user:
            return "User already exists"

        user = User(
            name=name,
            name3=name[:3].upper(),
            phone=phone,
            age=age,
            height=height,
            profession=profession,
            location=location,
            subscription_active=False
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("register.html")


# ---------------- COMMERCIAL LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    name3 = request.form.get("name3", "").upper().strip()
    phone = normalize_phone(request.form.get("phone"))

    user = User.query.filter_by(
        name3=name3,
        phone=phone
    ).first()

    if not user:
        return "Invalid credentials"

    session["user"] = user.phone
    session["role"] = "user"

    if user.subscription_active:
        return redirect(url_for("dashboard"))

    return redirect(url_for("subscribe"))


# ---------------- PERSONAL LOGIN ----------------

@app.route("/personal_login", methods=["POST"])
def personal_login():

    fullname = request.form.get("fullname")
    phone = normalize_phone(request.form.get("phone"))

    user = User.query.filter_by(phone=phone).first()

    if not user:

        user = User(
            name=fullname,
            name3=fullname[:3].upper(),
            phone=phone,
            subscription_active=False
        )

        db.session.add(user)
        db.session.commit()

    session["user"] = user.phone
    session["role"] = "user"

    return redirect(url_for("dashboard"))


# ---------------- SUBSCRIPTION ----------------

@app.route("/subscribe")
def subscribe():

    if session.get("role") != "user":
        return redirect(url_for("home"))

    return render_template("subscribe.html")


# ---------------- ACTIVATE SUBSCRIPTION ----------------

@app.route("/activate", methods=["POST"])
def activate():

    if session.get("role") != "user":
        return redirect(url_for("home"))

    user = User.query.filter_by(phone=session["user"]).first()

    if user:
        user.subscription_active = True
        db.session.commit()

    return redirect(url_for("dashboard"))


# ---------------- USER DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if session.get("role") != "user":
        return redirect(url_for("home"))

    return render_template("dashboard.html")


# ---------------- SEARCH USERS ----------------

@app.route("/search")
def search():

    if session.get("role") != "user":
        return redirect(url_for("home"))

    age = request.args.get("age")
    location = request.args.get("location")
    profession = request.args.get("profession")

    query = User.query

    if age:
        query = query.filter(User.age == age)

    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))

    if profession:
        query = query.filter(User.profession.ilike(f"%{profession}%"))

    users = query.all()

    return render_template("search.html", users=users)


# ---------------- CREATE AGENT ----------------

@app.route("/create-agent", methods=["POST"])
def create_agent():

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    existing = Agent.query.filter_by(email=email).first()

    if existing:
        return "Agent already exists"

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    agent = Agent(
        name=name,
        email=email,
        password_hash=password_hash
    )

    db.session.add(agent)
    db.session.commit()

    return "Agent created successfully"


# ---------------- AGENT LOGIN ----------------

@app.route("/agent-login", methods=["GET", "POST"])
def agent_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        agent = Agent.query.filter_by(email=email).first()

        if not agent:
            return "Agent not found"

        if not bcrypt.check_password_hash(agent.password_hash, password):
            return "Invalid password"

        session["role"] = "agent"
        session["agent"] = agent.email

        return redirect(url_for("agent_dashboard"))

    return render_template("agent_login.html")


# ---------------- AGENT DASHBOARD ----------------

@app.route("/agent-dashboard")
def agent_dashboard():

    if session.get("role") != "agent":
        return redirect(url_for("agent_login"))

    users = User.query.all()

    return render_template("agent_dashboard.html", users=users)


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))

        return "Invalid admin login"

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin-dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    users = User.query.count()
    agents = Agent.query.count()
    subscriptions = User.query.filter_by(subscription_active=True).count()

    return render_template(
        "admin_dashboard.html",
        users=users,
        agents=agents,
        subscriptions=subscriptions
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("home"))


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)