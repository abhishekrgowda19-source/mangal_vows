import os
from twilio.rest import Client
from models import User
from datetime import datetime, timedelta

TWILIO_SID          = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def send_whatsapp(to_phone, message):
    """Send WhatsApp message via Twilio"""
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:+91{to_phone}",
            body=message
        )
        print(f"  ✅ WhatsApp sent to {to_phone}")
    except Exception as e:
        print(f"  ❌ Failed to send to {to_phone}: {e}")


def send_expiry_reminders(app):
    """
    Runs every day — finds users expiring in 3 days
    and sends them a WhatsApp reminder
    """
    with app.app_context():
        now        = datetime.utcnow()
        three_days = now + timedelta(days=3)

        # Find users expiring within next 3 days
        expiring_users = User.query.filter(
            User.subscription_active == True,
            User.subscription_expiry != None,
            User.subscription_expiry >= now,
            User.subscription_expiry <= three_days
        ).all()

        print(f"\n⏰ Reminder check — {now.strftime('%d %b %Y %H:%M')}")
        print(f"   Found {len(expiring_users)} user(s) expiring in 3 days\n")

        for user in expiring_users:
            if not user.phone:
                continue

            expiry_date = user.subscription_expiry.strftime("%d %b %Y")

            message = (
                f"🙏 Dear {user.name},\n\n"
                f"Your Mangal Vows subscription is expiring on *{expiry_date}*.\n\n"
                f"Renew now for just ₹100 to continue finding your perfect match! 💍\n\n"
                f"👉 Renew here: https://mangal-vows.onrender.com/renew\n\n"
                f"– Team Mangal Vows"
            )

            send_whatsapp(user.phone, message)

        print(f"\n✅ Reminder job completed!\n")