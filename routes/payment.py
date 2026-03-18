from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from database import db
from models import User, Subscription
from datetime import datetime, timedelta
import razorpay
import hmac
import hashlib
import os

payment_bp = Blueprint("payment", __name__)

# ─── Razorpay client (reads from env variables) ───────────────────────────────
def get_razorpay_client():
    return razorpay.Client(auth=(
        os.environ.get("RAZORPAY_KEY_ID"),
        os.environ.get("RAZORPAY_KEY_SECRET")
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  PLAN CONFIG  (single place to change prices)
# ─────────────────────────────────────────────────────────────────────────────
PLANS = {
    "basic": {
        "amount":       50000,          # ₹500 in paise
        "label":        "₹500",
        "description":  "Basic Subscription – 30 days full access",
        "duration_days": 30,
    },
    "validation": {
        "amount":       10000,          # ₹100 in paise
        "label":        "₹100",
        "description":  "Validation Fee – Extend for 30 days",
        "duration_days": 30,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 ── CREATE RAZORPAY ORDER
#  Frontend calls this → gets order_id → opens Razorpay checkout popup
# ─────────────────────────────────────────────────────────────────────────────
@payment_bp.route("/payment/create-order", methods=["POST"])
def create_order():
    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 401

    data      = request.get_json()
    plan_type = data.get("plan_type", "basic")

    if plan_type not in PLANS:
        return jsonify({"error": "Invalid plan"}), 400

    plan = PLANS[plan_type]
    user = User.query.filter_by(phone=session["user"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        client = get_razorpay_client()

        # Create order on Razorpay
        rz_order = client.order.create({
            "amount":   plan["amount"],
            "currency": "INR",
            "receipt":  f"mv_{user.id[:8]}_{int(datetime.utcnow().timestamp())}",
            "notes": {
                "user_id":   user.id,
                "plan_type": plan_type,
                "user_name": user.name,
                "user_phone": user.phone,
            }
        })

        # Save pending subscription record
        sub = Subscription(
            user_id            = user.id,
            plan_type          = plan_type,
            amount_paid        = plan["amount"],
            razorpay_order_id  = rz_order["id"],
            status             = "pending",
        )
        db.session.add(sub)
        db.session.commit()

        return jsonify({
            "order_id":    rz_order["id"],
            "amount":      plan["amount"],
            "currency":    "INR",
            "key":         os.environ.get("RAZORPAY_KEY_ID"),
            "name":        "Mangal Vows",
            "description": plan["description"],
            "prefill": {
                "name":    user.name,
                "contact": user.phone,
                "email":   user.email or "",
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 ── VERIFY PAYMENT (called from frontend after Razorpay success)
#  We ALWAYS verify the signature — never trust frontend alone
# ─────────────────────────────────────────────────────────────────────────────
@payment_bp.route("/payment/verify", methods=["POST"])
def verify_payment():
    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    razorpay_order_id   = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature  = data.get("razorpay_signature")

    # ── Signature verification ──────────────────────────────────────────────
    secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    body   = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, razorpay_signature):
        return jsonify({"error": "Payment verification failed. Signature mismatch."}), 400

    # ── Find the pending subscription record ────────────────────────────────
    sub = Subscription.query.filter_by(
        razorpay_order_id=razorpay_order_id,
        status="pending"
    ).first()

    if not sub:
        return jsonify({"error": "Order not found"}), 404

    # ── Activate subscription ────────────────────────────────────────────────
    now      = datetime.utcnow()
    duration = PLANS[sub.plan_type]["duration_days"]

    sub.razorpay_payment_id = razorpay_payment_id
    sub.razorpay_signature  = razorpay_signature
    sub.status              = "paid"
    sub.starts_at           = now
    sub.expires_at          = now + timedelta(days=duration)

    # Update user
    user = User.query.get(sub.user_id)
    user.subscription_active     = True
    user.subscription_expires_at = sub.expires_at

    if sub.plan_type == "validation":
        user.validation_paid_at    = now
        user.validation_expires_at = sub.expires_at

    db.session.commit()

    return jsonify({
        "success":    True,
        "message":    "Payment verified! Subscription activated.",
        "expires_at": sub.expires_at.isoformat(),
        "days_left":  duration,
        "redirect":   "/dashboard"
    })


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 ── RAZORPAY WEBHOOK  (server-to-server, extra security layer)
#  Even if frontend fails, webhook activates the subscription
# ─────────────────────────────────────────────────────────────────────────────
@payment_bp.route("/payment/webhook", methods=["POST"])
def payment_webhook():
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    received_sig   = request.headers.get("X-Razorpay-Signature", "")
    payload        = request.get_data()

    # Verify webhook signature
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, received_sig):
        return jsonify({"error": "Invalid webhook signature"}), 400

    event = request.get_json()

    if event.get("event") == "payment.captured":
        payment    = event["payload"]["payment"]["entity"]
        order_id   = payment.get("order_id")
        payment_id = payment.get("id")

        sub = Subscription.query.filter_by(
            razorpay_order_id=order_id
        ).first()

        if sub and sub.status != "paid":
            now      = datetime.utcnow()
            duration = PLANS.get(sub.plan_type, PLANS["basic"])["duration_days"]

            sub.razorpay_payment_id = payment_id
            sub.status    = "paid"
            sub.starts_at = now
            sub.expires_at = now + timedelta(days=duration)

            user = User.query.get(sub.user_id)
            if user:
                user.subscription_active     = True
                user.subscription_expires_at = sub.expires_at
                if sub.plan_type == "validation":
                    user.validation_paid_at    = now
                    user.validation_expires_at = sub.expires_at

            db.session.commit()

    return jsonify({"status": "ok"}), 200


# ─────────────────────────────────────────────────────────────────────────────
#  SUBSCRIPTION STATUS  (real-time check for frontend)
# ─────────────────────────────────────────────────────────────────────────────
@payment_bp.route("/payment/status", methods=["GET"])
def subscription_status():
    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.filter_by(phone=session["user"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    is_valid = user.is_subscription_valid()

    return jsonify({
        "subscription_active":    is_valid,
        "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "days_until_expiry":      user.days_until_expiry(),
        "validation_valid":       user.is_validation_valid(),
        "validation_expires_at":  user.validation_expires_at.isoformat() if user.validation_expires_at else None,
        "needs_renewal":          is_valid and user.days_until_expiry() <= 3,
    })