from database import db
from datetime import datetime
import uuid
from sqlalchemy import Index, text


def generate_uuid():
    return str(uuid.uuid4())


# ---------------- USER ----------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    user_type = db.Column(db.String(20), default="commercial", index=True)

    # BASIC INFO
    name = db.Column(db.String(50), nullable=False)
    name3 = db.Column(db.String(10))

    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)

    # No unique=True here — partial unique index defined at bottom
    email = db.Column(db.String(100), nullable=True)

    age = db.Column(db.Integer)
    height = db.Column(db.String(10))

    gender = db.Column(db.String(10), default="other")

    # PERSONAL
    birth_place = db.Column(db.String(100))
    birth_time = db.Column(db.String(20))

    # PROFILE
    profession = db.Column(db.String(100))
    education = db.Column(db.String(100))

    caste = db.Column(db.String(100))
    community = db.Column(db.String(100))
    mother_tongue = db.Column(db.String(50))
    religion = db.Column(db.String(50))

    # LOCATION
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    location = db.Column(db.String(100))

    profile_photo_url = db.Column(db.Text)

    # RELATION
    agent_id = db.Column(
        db.String(36),
        db.ForeignKey("agents.id", ondelete="SET NULL")
    )

    # SUBSCRIPTION
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_expiry = db.Column(db.DateTime)
    subscription_started = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        if self.subscription_expiry and datetime.utcnow() > self.subscription_expiry:
            return True
        return False

    def needs_renewal(self):
        return self.subscription_started is not None and self.is_expired()

    def to_dict(self, viewer_subscription_active=False, viewer_type="commercial"):
        data = {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "height": self.height,
            "profession": self.profession,
            "education": self.education,
            "caste": self.caste,
            "community": self.community,
            "mother_tongue": self.mother_tongue,
            "religion": self.religion,
            "location": self.location,
            "city": self.city,
            "state": self.state,
            "subscription_active": self.subscription_active,
            "subscription_expiry": self.subscription_expiry
        }

        if viewer_type == "personal" and viewer_subscription_active:
            data["phone"] = self.phone
            data["email"] = self.email
            data["birth_place"] = self.birth_place
            data["birth_time"] = self.birth_time
        else:
            data["phone"] = "Subscribe to view"
            data["email"] = "Subscribe to view"
            data["birth_place"] = "Hidden"
            data["birth_time"] = "Hidden"

        return data


# ---------------- AGENT ----------------
class Agent(db.Model):
    __tablename__ = "agents"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    name = db.Column(db.String(100), nullable=False)

    # ✅ email max 30 chars at DB level
    email = db.Column(db.String(30), unique=True, nullable=False)
    phone = db.Column(db.String(15))

    password_hash = db.Column(db.Text, nullable=False)

    office_address = db.Column(db.Text)
    years_experience = db.Column(db.Integer)

    kyc_status = db.Column(db.String(20), default="pending", index=True)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    clients = db.relationship(
        "User",
        backref="agent",
        lazy=True,
        passive_deletes=True
    )


# ---------------- ADMIN ----------------
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # ✅ username max 15 chars at DB level
    username = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- PROPOSAL ----------------
class Proposal(db.Model):
    __tablename__ = "proposals"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    token = db.Column(db.String(64), unique=True, nullable=False)

    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"))
    client_id = db.Column(db.String(36), db.ForeignKey("users.id"))

    profile_ids = db.Column(db.Text)

    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    agent = db.relationship("Agent", backref="proposals")
    client = db.relationship("User", foreign_keys=[client_id])


# ---------------- PAYMENT ----------------
class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"))

    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))

    amount = db.Column(db.Integer)
    payment_type = db.Column(db.String(20), default="initial")
    status = db.Column(db.String(20), default="success", index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="payments")


# ---------------- DISPUTE ----------------
class Dispute(db.Model):
    __tablename__ = "disputes"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    raised_by_user = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    raised_by_agent = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True)
    against = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    ticket_type = db.Column(db.String(50), default="general", index=True)

    subject = db.Column(db.String(200))
    description = db.Column(db.Text)

    status = db.Column(db.String(20), default="open", index=True)
    admin_note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    reporter_user = db.relationship("User", foreign_keys=[raised_by_user])
    reporter_agent = db.relationship("Agent", foreign_keys=[raised_by_agent])
    reported = db.relationship("User", foreign_keys=[against])


# Partial unique index — only enforces uniqueness when email IS NOT NULL
# Allows multiple commercial users to have email=None without conflict
Index(
    "uq_users_email_not_null",
    User.email,
    unique=True,
    sqlite_where=text("email IS NOT NULL")
)