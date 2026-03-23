import razorpay
import hmac
import hashlib
import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User
from database import db
from datetime import datetime, timedelta

subscription = Blueprint("subscription", __name__)

RAZORPAY_KEY_ID     = os.environ.get("RAZORPAY_KEY_ID", "your_key_id")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "your_key_secret")

ACTIVATION_AMOUNT  = 50000   # ₹500 in paise
RENEWAL_AMOUNT     = 10000   # ₹100 in paise

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ─────────────────────────────────────────
# HELPER — Verify Razorpay Signature
# ─────────────────────────────────────────

def verify_signature(order_id, payment_id, signature):
    body = order_id + "|" + payment_id
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    return expected == signature


# ─────────────────────────────────────────
# ₹500 ACTIVATION — First time
# ─────────────────────────────────────────

@subscription.route("/subscribe")
def subscribe():
    if not session.get("user"):
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session["user"]).first()
    if not user_data:
        return redirect(url_for("user.home"))

    # If already active send to dashboard
    if user_data.subscription_active and user_data.subscription_expiry and \
       user_data.subscription_expiry > datetime.utcnow():
        return redirect(url_for("user.dashboard"))

    order = client.order.create({
        "amount":          ACTIVATION_AMOUNT,
        "currency":        "INR",
        "payment_capture": 1
    })

    return render_template(
        "subscribe.html",
        key_id=RAZORPAY_KEY_ID,
        order_id=order["id"],
        amount=ACTIVATION_AMOUNT,
        payment_type="activation"
    )


@subscription.route("/verify-payment", methods=["POST"])
def verify_payment():
    if not session.get("user"):
        return redirect(url_for("user.home"))

    order_id   = request.form.get("razorpay_order_id")
    payment_id = request.form.get("razorpay_payment_id")
    signature  = request.form.get("razorpay_signature")

    if not verify_signature(order_id, payment_id, signature):
        return render_template("subscribe.html", error="Payment verification failed. Please try again.")

    user_data = User.query.filter_by(phone=session["user"]).first()
    if user_data:
        user_data.subscription_active = True
        user_data.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        db.session.commit()

    return redirect(url_for("user.dashboard"))


# ─────────────────────────────────────────
# ₹100 RENEWAL — Every 30 days
# ─────────────────────────────────────────

@subscription.route("/renew")
def renew():
    if not session.get("user"):
        return redirect(url_for("user.home"))

    user_data = User.query.filter_by(phone=session["user"]).first()
    if not user_data:
        return redirect(url_for("user.home"))

    # If never subscribed → send to ₹500 activation
    if not user_data.subscription_active and not user_data.subscription_expiry:
        return redirect(url_for("subscription.subscribe"))

    order = client.order.create({
        "amount":          RENEWAL_AMOUNT,
        "currency":        "INR",
        "payment_capture": 1
    })

    return render_template(
        "renew.html",
        key_id=RAZORPAY_KEY_ID,
        order_id=order["id"],
        amount=RENEWAL_AMOUNT,
        user=user_data
    )


@subscription.route("/verify-renewal", methods=["POST"])
def verify_renewal():
    if not session.get("user"):
        return redirect(url_for("user.home"))

    order_id   = request.form.get("razorpay_order_id")
    payment_id = request.form.get("razorpay_payment_id")
    signature  = request.form.get("razorpay_signature")

    if not verify_signature(order_id, payment_id, signature):
        return render_template("renew.html", error="Payment verification failed. Please try again.")

    user_data = User.query.filter_by(phone=session["user"]).first()
    if user_data:
        # ✅ Extend from today if expired, or from expiry if still active
        base = datetime.utcnow()
        if user_data.subscription_expiry and user_data.subscription_expiry > base:
            base = user_data.subscription_expiry

        user_data.subscription_active = True
        user_data.subscription_expiry = base + timedelta(days=30)
        db.session.commit()

    return redirect(url_for("user.dashboard"))