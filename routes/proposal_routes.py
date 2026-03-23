import os
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Agent, Proposal
from database import db
from datetime import datetime, timedelta
from twilio.rest import Client

proposal_bp = Blueprint("proposal_bp", __name__)

TWILIO_SID            = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN     = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM  = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
APP_URL               = os.environ.get("APP_URL", "https://mangal-vows.onrender.com")


def send_whatsapp(to_phone, message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:+91{to_phone}",
            body=message
        )
        return True
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return False


# ── Select profiles to send ───────────────────────────

@proposal_bp.route("/agent-send-proposal/<client_id>", methods=["GET", "POST"])
def send_proposal(client_id):
    if session.get("role") != "agent":
        return redirect(url_for("agent_bp.agent_login"))

    agent = Agent.query.get(session.get("agent"))
    client = User.query.get(client_id)

    if not agent or not client:
        return redirect(url_for("agent_bp.agent_dashboard"))

    # All users except the client
    all_profiles = User.query.filter(User.id != client_id).all()

    if request.method == "POST":
        selected_ids = request.form.getlist("profile_ids")

        if len(selected_ids) < 1:
            return render_template(
                "send_proposal.html",
                agent=agent,
                client=client,
                profiles=all_profiles,
                error="Please select at least 1 profile"
            )

        if len(selected_ids) > 5:
            return render_template(
                "send_proposal.html",
                agent=agent,
                client=client,
                profiles=all_profiles,
                error="You can select maximum 5 profiles"
            )

        # ✅ Create secure token
        token = secrets.token_urlsafe(32)

        proposal = Proposal(
            token       = token,
            agent_id    = agent.id,
            client_id   = client_id,
            profile_ids = ",".join(selected_ids),
            expires_at  = datetime.utcnow() + timedelta(days=7)  # expires in 7 days
        )
        db.session.add(proposal)
        db.session.commit()

        # ✅ Build secure link
        proposal_link = f"{APP_URL}/view-proposal/{token}"

        # ✅ Send WhatsApp
        message = (
            f"🙏 Dear {client.name},\n\n"
            f"Your matchmaking agent *{agent.name}* has curated "
            f"*{len(selected_ids)} profile(s)* especially for you! 💍\n\n"
            f"👉 View your matches here:\n{proposal_link}\n\n"
            f"⏰ This link expires in 7 days.\n\n"
            f"– Team Mangal Vows"
        )

        sent = send_whatsapp(client.phone, message)

        if sent:
            return render_template(
                "send_proposal.html",
                agent=agent,
                client=client,
                profiles=all_profiles,
                success=f"✅ Proposal sent to {client.name} on WhatsApp!"
            )
        else:
            return render_template(
                "send_proposal.html",
                agent=agent,
                client=client,
                profiles=all_profiles,
                error="❌ Failed to send WhatsApp. Check Twilio credentials."
            )

    return render_template(
        "send_proposal.html",
        agent=agent,
        client=client,
        profiles=all_profiles
    )


# ── View proposal via secure link ────────────────────

@proposal_bp.route("/view-proposal/<token>")
def view_proposal(token):
    proposal = Proposal.query.filter_by(token=token).first()

    if not proposal:
        return render_template("proposal_expired.html", reason="Invalid link")

    if proposal.expires_at < datetime.utcnow():
        return render_template("proposal_expired.html", reason="This link has expired")

    client  = User.query.get(proposal.client_id)
    agent   = Agent.query.get(proposal.agent_id)

    profile_ids = proposal.profile_ids.split(",")
    profiles    = User.query.filter(User.id.in_(profile_ids)).all()

    return render_template(
        "view_proposal.html",
        client=client,
        agent=agent,
        profiles=profiles,
        expires_at=proposal.expires_at
    )