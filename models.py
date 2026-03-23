from database import db
from datetime import datetime
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    id                  = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name                = db.Column(db.String(100), nullable=False)
    name3               = db.Column(db.String(3))
    phone               = db.Column(db.String(15), unique=True, nullable=False)
    email               = db.Column(db.String(120))
    age                 = db.Column(db.Integer)
    height              = db.Column(db.String(10))
    gender              = db.Column(db.String(10))
    profession          = db.Column(db.String(100))
    education           = db.Column(db.String(100))
    caste               = db.Column(db.String(100))
    community           = db.Column(db.String(100))
    mother_tongue       = db.Column(db.String(50))
    religion            = db.Column(db.String(50))
    location            = db.Column(db.String(100))
    city                = db.Column(db.String(100))
    state               = db.Column(db.String(100))
    profile_photo_url   = db.Column(db.Text)
    agent_id            = db.Column(db.String(36), db.ForeignKey("agents.id"))
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_expiry = db.Column(db.DateTime)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "phone": self.phone,
            "age": self.age, "gender": self.gender, "caste": self.caste,
            "profession": self.profession, "location": self.location,
        }


class Agent(db.Model):
    __tablename__ = "agents"

    id               = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name             = db.Column(db.String(100), nullable=False)
    email            = db.Column(db.String(120), unique=True, nullable=False)
    phone            = db.Column(db.String(15))
    password_hash    = db.Column(db.Text, nullable=False)
    office_address   = db.Column(db.Text)
    years_experience = db.Column(db.Integer)
    kyc_status       = db.Column(db.String(20), default="pending")
    is_active        = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    clients = db.relationship("User", backref="agent", lazy=True)


class Admin(db.Model):
    __tablename__ = "admins"

    id            = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username      = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Proposal(db.Model):
    __tablename__ = "proposals"

    id          = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    token       = db.Column(db.String(64), unique=True, nullable=False)
    agent_id    = db.Column(db.String(36), db.ForeignKey("agents.id"))
    client_id   = db.Column(db.String(36), db.ForeignKey("users.id"))
    profile_ids = db.Column(db.Text)
    expires_at  = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    agent  = db.relationship("Agent", backref="proposals")
    client = db.relationship("User", foreign_keys=[client_id])


# ✅ NEW — Payment tracking
class Payment(db.Model):
    __tablename__ = "payments"

    id             = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id        = db.Column(db.String(36), db.ForeignKey("users.id"))
    razorpay_order_id   = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    amount         = db.Column(db.Integer)   # in paise
    payment_type   = db.Column(db.String(20))  # "activation" or "renewal"
    status         = db.Column(db.String(20), default="success")
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="payments")


# ✅ NEW — Dispute management
class Dispute(db.Model):
    __tablename__ = "disputes"

    id          = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    raised_by   = db.Column(db.String(36), db.ForeignKey("users.id"))
    against     = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    subject     = db.Column(db.String(200))
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default="open")  # open, resolved, closed
    admin_note  = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    reporter = db.relationship("User", foreign_keys=[raised_by])
    reported = db.relationship("User", foreign_keys=[against])