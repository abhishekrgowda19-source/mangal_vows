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
AMOUNT_PAISE        = 50000  # ₹500 in paise

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ----------------------------------------
# SUBSCRIBE PAGE — creates Razorpay order
# ----------------------------------------

@subscription.route("/subscribe")
def subscribe():
    if not session.get("user"):
        return redirect(url_for("user.home"))

    order = client.order.create({
        "amount":   AMOUNT_PAISE,
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template(
        "subscribe.html",
        key_id=RAZORPAY_KEY_ID,
        order_id=order["id"],
        amount=AMOUNT_PAISE
    )


# ----------------------------------------
# PAYMENT VERIFICATION
# ----------------------------------------

@subscription.route("/verify-payment", methods=["POST"])
def verify_payment():
    if not session.get("user"):
        return redirect(url_for("user.home"))

    razorpay_order_id   = request.form.get("razorpay_order_id")
    razorpay_payment_id = request.form.get("razorpay_payment_id")
    razorpay_signature  = request.form.get("razorpay_signature")

    # Verify signature
    body = razorpay_order_id + "|" + razorpay_payment_id
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected_signature != razorpay_signature:
        return render_template("subscribe.html", error="Payment verification failed. Please try again.")

    # Activate subscription
    user = User.query.filter_by(phone=session["user"]).first()
    if user:
        user.subscription_active = True
        user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        db.session.commit()

    return redirect(url_for("user.dashboard"))