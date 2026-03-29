import razorpay
import hmac
import hashlib
import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Payment
from database import db
from datetime import datetime, timedelta

subscription = Blueprint("subscription", __name__)

RAZORPAY_KEY_ID     = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

INITIAL_AMOUNT = 50000   # ₹500 in paise
RENEWAL_AMOUNT = 10000   # ₹100 in paise


def verify_signature(order_id, payment_id, signature):
    body     = order_id + "|" + payment_id
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    return expected == signature


# ---------------- INITIAL SUBSCRIBE (₹500) ----------------
@subscription.route("/subscribe")
def subscribe():
    if not session.get("user_id"):
        return redirect(url_for("user.login"))

    try:
        order = client.order.create({
            "amount":          INITIAL_AMOUNT,
            "currency":        "INR",
            "payment_capture": 1
        })
    except Exception:
        return render_template("subscribe.html",
                               key_id=RAZORPAY_KEY_ID,
                               order_id=None,
                               amount=INITIAL_AMOUNT,
                               payment_type="initial",
                               error="Payment gateway error. Please try again.")

    return render_template(
        "subscribe.html",
        key_id=RAZORPAY_KEY_ID,
        order_id=order["id"],
        amount=INITIAL_AMOUNT,
        payment_type="initial"
    )


# ---------------- RENEWAL (₹100) ----------------
@subscription.route("/renew")
def renew():
    if not session.get("user_id"):
        return redirect(url_for("user.login"))

    user = User.query.get(session["user_id"])

    if not user:
        return redirect(url_for("user.login"))

    # ✅ If they never subscribed at all, force full payment
    if not user.needs_renewal():
        return redirect(url_for("subscription.subscribe"))

    try:
        order = client.order.create({
            "amount":          RENEWAL_AMOUNT,
            "currency":        "INR",
            "payment_capture": 1
        })
    except Exception:
        return render_template("subscribe.html",
                               key_id=RAZORPAY_KEY_ID,
                               order_id=None,
                               amount=RENEWAL_AMOUNT,
                               payment_type="renewal",
                               error="Payment gateway error. Please try again.")

    return render_template(
        "subscribe.html",
        key_id=RAZORPAY_KEY_ID,
        order_id=order["id"],
        amount=RENEWAL_AMOUNT,
        payment_type="renewal"
    )


# ---------------- VERIFY PAYMENT ----------------
@subscription.route("/verify-payment", methods=["POST"])
def verify_payment():
    if not session.get("user_id"):
        return redirect(url_for("user.login"))

    order_id     = request.form.get("razorpay_order_id")
    payment_id   = request.form.get("razorpay_payment_id")
    signature    = request.form.get("razorpay_signature")
    payment_type = request.form.get("payment_type", "initial")

    if not order_id or not payment_id or not signature:
        return render_template("subscribe.html",
                               key_id=RAZORPAY_KEY_ID,
                               order_id=None,
                               amount=INITIAL_AMOUNT,
                               payment_type=payment_type,
                               error="Incomplete payment data. Please try again.")

    if not verify_signature(order_id, payment_id, signature):
        return render_template("subscribe.html",
                               key_id=RAZORPAY_KEY_ID,
                               order_id=None,
                               amount=INITIAL_AMOUNT,
                               payment_type=payment_type,
                               error="Payment verification failed. Contact support.")

    user = User.query.get(session["user_id"])

    user.subscription_active = True
    user.subscription_expiry = datetime.utcnow() + timedelta(days=30)

    # ✅ Track first subscription date
    if payment_type == "initial" or not user.subscription_started:
        user.subscription_started = datetime.utcnow()

    amount = RENEWAL_AMOUNT if payment_type == "renewal" else INITIAL_AMOUNT

    payment = Payment(
        user_id=user.id,
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        amount=amount,
        payment_type=payment_type,
        status="success"
    )

    db.session.add(payment)
    db.session.commit()

    return redirect(url_for("user.dashboard"))