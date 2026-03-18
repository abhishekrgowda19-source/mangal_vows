from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from config import Config
from database import db
from models import User, Agent
from routes.payment import payment_bp
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

db.init_app(app)
bcrypt = Bcrypt(app)

# ── Register blueprints ──────────────────────────────────────────────────────
app.register_blueprint(payment_bp)

# ── Admin panel ──────────────────────────────────────────────────────────────
class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get("role") == "admin"
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin_login"))

admin = Admin(app, name="Mangal Vows Admin")
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Agent, db.session))

with app.app_context():
    db.create_all()


# ── Helpers ──────────────────────────────────────────────────────────────────
def normalize_phone(phone):
    if not phone:
        return ""
    return ''.join(filter(str.isdigit, phone))[-10:]

def current_user():
    """Return the logged-in User object with real-time subscription check."""
    phone = session.get("user")
    if not phone:
        return None
    user = User.query.filter_by(phone=phone).first()
    if user:
        # Real-time expiry check on every request
        user.is_subscription_valid()
    return user


# ── HOME ─────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("login.html")


# ── REGISTER ─────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name       = request.form["name"].strip()
        phone      = normalize_phone(request.form["phone"])
        age        = request.form.get("age")
        height     = request.form.get("height")
        profession = request.form.get("profession")
        location   = request.form.get("location")
        community  = request.form.get("community", "")
        mother_tongue = request.form.get("mother_tongue", "")
        religion   = request.form.get("religion", "")

        if not name or not phone:
            return render_template("register.html", error="Name and phone are required.")

        if len(phone) != 10:
            return render_template("register.html", error="Enter a valid 10-digit phone number.")

        if User.query.filter_by(phone=phone).first():
            return render_template("register.html", error="Phone number already registered.")

        user = User(
            name          = name,
            name3         = name[:3].upper(),
            phone         = phone,
            age           = int(age) if age else None,
            height        = height,
            profession    = profession,
            location      = location,
            community     = community,
            mother_tongue = mother_tongue,
            religion      = religion,
            subscription_active = False
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("register.html")


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    name3 = request.form.get("name3", "").upper().strip()
    phone = normalize_phone(request.form.get("phone"))
    user  = User.query.filter_by(name3=name3, phone=phone).first()

    if not user:
        return render_template("login.html", error="Invalid credentials.")

    session["user"] = user.phone
    session["role"] = "user"

    # Real-time subscription check
    if user.is_subscription_valid():
        return redirect(url_for("dashboard"))
    return redirect(url_for("subscribe"))


# ── PERSONAL LOGIN ───────────────────────────────────────────────────────────
@app.route("/personal_login", methods=["POST"])
def personal_login():
    fullname = request.form.get("fullname", "").strip()
    phone    = normalize_phone(request.form.get("phone"))

    if not fullname or not phone:
        return render_template("login.html", error="Name and phone required.")

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

    if user.is_subscription_valid():
        return redirect(url_for("dashboard"))
    return redirect(url_for("subscribe"))


# ── SUBSCRIBE PAGE ────────────────────────────────────────────────────────────
@app.route("/subscribe")
def subscribe():
    if session.get("role") != "user":
        return redirect(url_for("home"))
    return render_template("subscribe.html")


# ── DASHBOARD ────────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if session.get("role") != "user":
        return redirect(url_for("home"))

    user = current_user()
    if not user:
        return redirect(url_for("home"))

    # Real-time guard — if subscription expired, redirect to subscribe
    if not user.is_subscription_valid():
        return redirect(url_for("subscribe"))

    return render_template("dashboard.html", user=user)


# ── SEARCH ───────────────────────────────────────────────────────────────────
@app.route("/search")
def search():
    if session.get("role") != "user":
        return redirect(url_for("home"))

    user = current_user()
    if not user or not user.is_subscription_valid():
        return redirect(url_for("subscribe"))

    age        = request.args.get("age")
    location   = request.args.get("location")
    profession = request.args.get("profession")
    community  = request.args.get("community")
    mother_tongue = request.args.get("mother_tongue")
    religion   = request.args.get("religion")
    height     = request.args.get("height")

    query = User.query.filter(User.phone != user.phone)  # exclude self

    if age:
        query = query.filter(User.age == int(age))
    if location:
        query = query.filter(User.location.ilike(f"%{location}%"))
    if profession:
        query = query.filter(User.profession.ilike(f"%{profession}%"))
    if community:
        query = query.filter(User.community.ilike(f"%{community}%"))
    if mother_tongue:
        query = query.filter(User.mother_tongue.ilike(f"%{mother_tongue}%"))
    if religion:
        query = query.filter(User.religion.ilike(f"%{religion}%"))
    if height:
        query = query.filter(User.height == height)

    users = query.all()
    return render_template("search.html", users=users)


# ── AGENT LOGIN ───────────────────────────────────────────────────────────────
@app.route("/agent-login", methods=["GET", "POST"])
def agent_login():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]
        agent    = Agent.query.filter_by(email=email).first()

        if not agent:
            return render_template("agent_login.html", error="Agent not found.")
        if not bcrypt.check_password_hash(agent.password_hash, password):
            return render_template("agent_login.html", error="Invalid password.")

        session["role"]  = "agent"
        session["agent"] = agent.email
        return redirect(url_for("agent_dashboard"))

    return render_template("agent_login.html")


# ── AGENT DASHBOARD ───────────────────────────────────────────────────────────
@app.route("/agent-dashboard")
def agent_dashboard():
    if session.get("role") != "agent":
        return redirect(url_for("agent_login"))
    users = User.query.all()
    return render_template("agent_dashboard.html", users=users)


# ── ADMIN LOGIN ───────────────────────────────────────────────────────────────
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Load from env — never hardcode
        admin_user = os.environ.get("ADMIN_USERNAME", "admin")
        admin_pass = os.environ.get("ADMIN_PASSWORD", "")
        if username == admin_user and password == admin_pass:
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid credentials.")
    return render_template("admin_login.html")


# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    total_users     = User.query.count()
    total_agents    = Agent.query.count()
    active_subs     = User.query.filter_by(subscription_active=True).count()
    expired_subs    = User.query.filter(
        User.subscription_active == False,
        User.subscription_expires_at != None
    ).count()

    return render_template(
        "admin_dashboard.html",
        users=total_users,
        agents=total_agents,
        subscriptions=active_subs,
        expired=expired_subs
    )


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)