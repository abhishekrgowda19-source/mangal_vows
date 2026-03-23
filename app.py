import os
from flask import Flask, redirect, session
from config import Config
from database import db
from models import User, Agent, Admin
from flask_admin import Admin as FlaskAdmin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt

from routes.user_routes import user
from routes.subscription_routes import subscription
from routes.admin_routes import admin_bp
from routes.agent_routes import agent_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)


# ── Flask-Admin Panel ─────────────────────────────────

class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get("role") == "admin"
    def inaccessible_callback(self, name, **kwargs):
        return redirect("/admin-login")


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


admin_panel = FlaskAdmin(app, name="Mangal Vows Admin", url="/admin")
admin_panel.add_view(SecureModelView(User,  db.session, endpoint="user_admin"))
admin_panel.add_view(AgentAdminView(Agent,  db.session, endpoint="agent_admin"))
admin_panel.add_view(AdminAdminView(Admin,  db.session, endpoint="admin_admin"))


# ── Blueprints ────────────────────────────────────────

app.register_blueprint(user)
app.register_blueprint(subscription)
app.register_blueprint(admin_bp)
app.register_blueprint(agent_bp)


# ── DB Init ───────────────────────────────────────────

with app.app_context():
    db.create_all()

    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "change-me-in-prod")

    if not Admin.query.filter_by(username=admin_username).first():
        hashed_pw = bcrypt.generate_password_hash(admin_password).decode("utf-8")
        db.session.add(Admin(username=admin_username, password_hash=hashed_pw))
        db.session.commit()


# ── Run ───────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=Config.DEBUG)