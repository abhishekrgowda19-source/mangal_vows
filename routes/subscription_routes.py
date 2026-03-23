from flask import Blueprint, request, jsonify, session, redirect, url_for
from models import User
from database import db
from datetime import datetime, timedelta
import razorpay
import os

subscription = Blueprint("subscription", __name__)

# ----------------------------------------
# RAZORPAY CLIENT
# ----------------------------------------

client = razorpay.Client(auth=(
    os.environ.get("RAZORPAY_KEY_ID"),
    os.environ.get("RAZORPAY_KEY_SECRET")
))

# ----------------------------------------
# CREATE ORDER
# ----------------------------------------

@subscription.route("/create-order", methods=["POST"])
def create_order():

    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        order = client.order.create({
            "amount": 50000,  # ₹500 in paise
            "currency": "INR",
            "payment_capture": 1
        })

        return jsonify(order)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------
# VERIFY PAYMENT
# ----------------------------------------

@subscription.route("/verify-payment", methods=["POST"])
def verify_payment():

    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    try:
        # Verify Razorpay signature
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.get("order_id"),
            "razorpay_payment_id": data.get("payment_id"),
            "razorpay_signature": data.get("signature")
        })

        # Activate subscription
        user = User.query.filter_by(phone=session.get("user")).first()

        if user:
            user.subscription_active = True
            user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
            db.session.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 400


# ----------------------------------------
# OPTIONAL: MANUAL ACTIVATE (TEST MODE)
# ----------------------------------------

@subscription.route("/activate", methods=["POST"])
def activate():

    if session.get("role") != "user":
        return redirect(url_for("user.home"))

    user = User.query.filter_by(phone=session.get("user")).first()

    if not user:
        return redirect(url_for("user.home"))

    user.subscription_active = True
    user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
    db.session.commit()

    return redirect(url_for("user.dashboard"))