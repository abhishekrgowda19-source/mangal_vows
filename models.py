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
            "id":         self.id,
            "name":       self.name,
            "phone":      self.phone,
            "age":        self.age,
            "gender":     self.gender,
            "caste":      self.caste,
            "profession": self.profession,
            "location":   self.location,
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


# ✅ NEW — Proposal model
class Proposal(db.Model):
    __tablename__ = "proposals"

    id         = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    token      = db.Column(db.String(64), unique=True, nullable=False)  # secure link token
    agent_id   = db.Column(db.String(36), db.ForeignKey("agents.id"))
    client_id  = db.Column(db.String(36), db.ForeignKey("users.id"))
    profile_ids = db.Column(db.Text)  # comma separated user ids
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    agent  = db.relationship("Agent", backref="proposals")
    client = db.relationship("User", foreign_keys=[client_id])