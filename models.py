from database import db
from datetime import datetime, timedelta
import uuid


def generate_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────
#  USER MODEL
# ─────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id               = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name             = db.Column(db.String(100), nullable=False)
    name3            = db.Column(db.String(3))
    phone            = db.Column(db.String(15), unique=True, nullable=False)
    email            = db.Column(db.String(120))

    # Bio
    age              = db.Column(db.Integer)
    height           = db.Column(db.String(10))   # e.g. "5'8"
    weight           = db.Column(db.Integer)
    gender           = db.Column(db.String(10))

    # Professional
    profession       = db.Column(db.String(100))
    education        = db.Column(db.String(100))

    # Cultural
    community        = db.Column(db.String(100))
    mother_tongue    = db.Column(db.String(50))
    religion         = db.Column(db.String(50))

    # Location
    location         = db.Column(db.String(100))
    city             = db.Column(db.String(100))
    state            = db.Column(db.String(100))

    # Media
    profile_photo_url = db.Column(db.Text)

    # Subscription
    subscription_active     = db.Column(db.Boolean, default=False)
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    validation_paid_at      = db.Column(db.DateTime, nullable=True)
    validation_expires_at   = db.Column(db.DateTime, nullable=True)

    # Agent link
    agent_id         = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True)

    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions    = db.relationship("Subscription", backref="user", lazy=True)

    def is_subscription_valid(self):
        """Real-time check — not just a boolean flag."""
        if not self.subscription_active:
            return False
        if self.subscription_expires_at and datetime.utcnow() > self.subscription_expires_at:
            # Auto-expire
            self.subscription_active = False
            db.session.commit()
            return False
        return True

    def is_validation_valid(self):
        """Check if 30-day validation is still active."""
        if not self.validation_expires_at:
            return False
        return datetime.utcnow() < self.validation_expires_at

    def days_until_expiry(self):
        """How many days left in subscription."""
        if not self.subscription_expires_at:
            return 0
        delta = self.subscription_expires_at - datetime.utcnow()
        return max(0, delta.days)

    def to_dict(self):
        return {
            "id":                     self.id,
            "name":                   self.name,
            "phone":                  self.phone,
            "age":                    self.age,
            "height":                 self.height,
            "profession":             self.profession,
            "education":              self.education,
            "community":              self.community,
            "mother_tongue":          self.mother_tongue,
            "religion":               self.religion,
            "location":               self.location,
            "city":                   self.city,
            "state":                  self.state,
            "profile_photo_url":      self.profile_photo_url,
            "subscription_active":    self.is_subscription_valid(),
            "subscription_expires_at": self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            "days_until_expiry":      self.days_until_expiry(),
            "validation_valid":       self.is_validation_valid(),
        }


# ─────────────────────────────────────────
#  SUBSCRIPTION MODEL  (real payment record)
# ─────────────────────────────────────────
class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id                   = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id              = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    plan_type            = db.Column(db.String(20), default="basic")   # basic | validation
    amount_paid          = db.Column(db.Integer, nullable=False)        # in paise (50000 = ₹500)

    # Razorpay fields
    razorpay_order_id    = db.Column(db.String(100), unique=True)
    razorpay_payment_id  = db.Column(db.String(100))
    razorpay_signature   = db.Column(db.Text)

    # Status
    status               = db.Column(db.String(20), default="pending")  # pending | paid | failed

    starts_at            = db.Column(db.DateTime)
    expires_at           = db.Column(db.DateTime)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":                  self.id,
            "plan_type":           self.plan_type,
            "amount_paid":         self.amount_paid / 100,   # convert paise → rupees
            "razorpay_order_id":   self.razorpay_order_id,
            "razorpay_payment_id": self.razorpay_payment_id,
            "status":              self.status,
            "starts_at":           self.starts_at.isoformat() if self.starts_at else None,
            "expires_at":          self.expires_at.isoformat() if self.expires_at else None,
        }


# ─────────────────────────────────────────
#  AGENT MODEL
# ─────────────────────────────────────────
class Agent(db.Model):
    __tablename__ = "agents"

    id                = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name              = db.Column(db.String(100), nullable=False)
    email             = db.Column(db.String(120), unique=True, nullable=False)
    phone             = db.Column(db.String(15))
    password_hash     = db.Column(db.Text, nullable=False)

    # KYC
    office_address    = db.Column(db.Text)
    years_experience  = db.Column(db.Integer)
    kyc_document_url  = db.Column(db.Text)
    kyc_status        = db.Column(db.String(20), default="pending")  # pending|approved|rejected

    # Revenue
    commission_rate   = db.Column(db.Float, default=10.0)   # 10% default
    total_earnings    = db.Column(db.Float, default=0.0)

    is_active         = db.Column(db.Boolean, default=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    clients           = db.relationship("User", backref="agent", lazy=True)