import os
from dotenv import load_dotenv

# ✅ Explicitly load .env from the same directory as app.py
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ✅ Diagnostic — remove this after confirming it works
print(">>> DATABASE_URL:", os.getenv("DATABASE_URL"))

from flask import Flask, redirect, session, url_for, send_from_directory
from config import Config
from database import db, bcrypt
from models import User, Agent, Admin
from flask_migrate import Migrate
from flask_admin import Admin as FlaskAdmin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler

# 🔹 ROUTES
from routes.user_routes import user
from routes.subscription_routes import subscription
from routes.admin_routes import admin_bp
from routes.agent_routes import agent_bp
from routes.proposal_routes import proposal_bp

# ✅ TICKET ROUTE
from routes.ticket import ticket_bp

from routes.reminder import send_expiry_reminders


# ── LOGIN REQUIRED DECORATOR ─────────────────────────
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if role and session.get("role") != role:
                return redirect(url_for("user.login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ── CREATE APP ─────────────────────────
from routes.api_routes import api_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(api_bp)

    if not os.environ.get("SECRET_KEY"):
        raise ValueError("SECRET_KEY environment variable is required")

    app.secret_key = os.environ["SECRET_KEY"]

    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    # 🔥 REGISTER BLUEPRINTS
    app.register_blueprint(user)
    app.register_blueprint(subscription)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(proposal_bp)
    app.register_blueprint(ticket_bp)

    # ── PWA ROUTES ─────────────────────────
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory('static', 'manifest.json')

    @app.route('/sw.js')
    def service_worker():
        return send_from_directory('static', 'sw.js')

    # ── OFFLINE PAGE ─────────────────────────
    @app.route('/offline')
    def offline():
        return '''
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Offline - Mangal Vows</title>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body {
                    font-family: sans-serif;
                    text-align: center;
                    padding: 60px 20px;
                    background: #111827;
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }
                .emoji { font-size: 64px; margin-bottom: 20px; }
                h2 { color: #d4a017; font-size: 24px; margin-bottom: 12px; }
                p { color: #9ca3af; margin-bottom: 24px; font-size: 15px; }
                a {
                    background: #d4a017;
                    color: #111827;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="emoji">📵</div>
            <h2>You are offline</h2>
            <p>Please check your internet connection and try again.</p>
            <a href="/">Try Again</a>
        </body>
        </html>
        '''

    # ── SECURITY HEADERS ─────────────────────────
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # ── ADMIN PANEL SECURITY ─────────────────────────
    class MyAdminIndexView(AdminIndexView):
        def is_accessible(self):
            return session.get("role") == "admin"

        def inaccessible_callback(self, name, **kwargs):
            return redirect(url_for("admin_bp.admin_login"))

    class SecureModelView(ModelView):
        def is_accessible(self):
            return session.get("role") == "admin"

        def inaccessible_callback(self, name, **kwargs):
            return redirect(url_for("admin_bp.admin_login"))

    # ✅ IMPROVED: added email to Flask Admin user view
    class UserAdminView(SecureModelView):
        column_list = (
            "name",
            "phone",
            "email",
            "city",
            "birth_place",
            "birth_time",
            "subscription_active"
        )

    class AgentAdminView(SecureModelView):
        def on_model_change(self, form, model, is_created):
            if form.password_hash.data:
                model.password_hash = bcrypt.generate_password_hash(
                    form.password_hash.data
                ).decode("utf-8")

    class AdminAdminView(SecureModelView):
        def on_model_change(self, form, model, is_created):
            if form.password_hash.data:
                model.password_hash = bcrypt.generate_password_hash(
                    form.password_hash.data
                ).decode("utf-8")

    admin_panel = FlaskAdmin(
        app,
        name="Mangal Vows Admin",
        url="/admin",
        template_mode="bootstrap4",
        index_view=MyAdminIndexView()
    )

    admin_panel.add_view(UserAdminView(User, db.session, name="Users", endpoint="admin_users_view"))
    admin_panel.add_view(AgentAdminView(Agent, db.session, name="Agents", endpoint="admin_agents_view"))
    admin_panel.add_view(AdminAdminView(Admin, db.session, name="Admins", endpoint="admin_admins_view"))

    # ── CLI COMMAND ─────────────────────────
    @app.cli.command("init-db")
    def init_db():
        db.create_all()

        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "mangaladmin@123")

        if not Admin.query.filter_by(username=admin_username).first():
            hashed_pw = bcrypt.generate_password_hash(admin_password).decode("utf-8")
            db.session.add(Admin(username=admin_username, password_hash=hashed_pw))
            db.session.commit()
            print(f"✅ Admin created: {admin_username}")

    # ── SCHEDULER ─────────────────────────
    def init_scheduler():
        if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            return

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=send_expiry_reminders,
            args=[app],
            trigger="cron",
            hour=9,
            minute=0,
            id="expiry_reminder"
        )
        scheduler.start()
        print("✅ Reminder scheduler started")

    init_scheduler()

    return app


# ── RUN APP ─────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(
        debug=app.config["DEBUG"],
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )