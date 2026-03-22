from flask import Flask, redirect
from config import Config
from database import db
from models import User, Agent, Admin
from flask_admin import Admin as FlaskAdmin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt
import os

# IMPORT ROUTES
from user_routes import user
from subscription_routes import subscription

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

db.init_app(app)
bcrypt = Bcrypt(app)

# ======================================================
# ADMIN PANEL
# ======================================================

class SecureModelView(ModelView):
    def is_accessible(self):
        from flask import session
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

admin_panel.add_view(SecureModelView(User, db.session, endpoint="user_admin"))
admin_panel.add_view(AgentAdminView(Agent, db.session, endpoint="agent_admin"))
admin_panel.add_view(AdminAdminView(Admin, db.session, endpoint="admin_admin"))

# ======================================================
# REGISTER BLUEPRINTS
# ======================================================

app.register_blueprint(user)
app.register_blueprint(subscription)

# ======================================================
# DB INIT
# ======================================================

with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username="admin").first():
        hashed_pw = bcrypt.generate_password_hash("admin123").decode("utf-8")
        db.session.add(Admin(username="admin", password_hash=hashed_pw))
        db.session.commit()

# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    app.run()