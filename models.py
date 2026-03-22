from database import db
from datetime import datetime
import uuid


def generate_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────
# USER MODEL
# ─────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id       = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name     = db.Column(db.String(100), nullable=False)
    name3    = db.Column(db.String(3))
    phone    = db.Column(db.String(15), unique=True, nullable=False)
    email    = db.Column(db.String(120))

    # Basic Info
    age      = db.Column(db.Integer)
    height   = db.Column(db.String(10))
    gender   = db.Column(db.String(10))

    # Professional
    profession = db.Column(db.String(100))
    education  = db.Column(db.String(100))

    # Cultural
    community       = db.Column(db.String(100))
    mother_tongue   = db.Column(db.String(50))
    religion        = db.Column(db.String(50))

    # Location
    location = db.Column(db.String(100))
    city     = db.Column(db.String(100))
    state    = db.Column(db.String(100))

    # Media
    profile_photo_url = db.Column(db.Text)

    # Agent link
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"))

    # ✅ SUBSCRIPTION (FULL)
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_expiry = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "age": self.age,
            "profession": self.profession,
            "location": self.location,
        }


# ─────────────────────────────────────────
# AGENT MODEL
# ─────────────────────────────────────────
class Agent(db.Model):
    __tablename__ = "agents"

    id            = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    phone         = db.Column(db.String(15))
    password_hash = db.Column(db.Text, nullable=False)

    # KYC
    office_address   = db.Column(db.Text)
    years_experience = db.Column(db.Integer)
    kyc_status       = db.Column(db.String(20), default="pending")

    # Status
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    clients = db.relationship(
        "User",
        backref="agent",
        lazy=True
    )


# ─────────────────────────────────────────
# ADMIN MODEL
# ─────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = "admins"

    id            = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username      = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)