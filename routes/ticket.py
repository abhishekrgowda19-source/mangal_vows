# routes/ticket.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import Dispute
from database import db
from datetime import datetime

ticket_bp = Blueprint("ticket_bp", __name__)


# ---------------- RAISE TICKET ----------------
@ticket_bp.route("/raise-ticket", methods=["GET", "POST"])
def raise_ticket():

    role = session.get("role")

    if not role or role == "admin":
        return redirect(url_for("user.login"))

    if request.method == "POST":

        subject     = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        ticket_type = request.form.get("ticket_type", "general").strip()

        if not subject or not description:
            return render_template(
                "raise_ticket.html",
                error="Subject and description are required."
            )

        ticket = Dispute(
            subject=subject,
            description=description,
            ticket_type=ticket_type,
            status="open",
            raised_by_user=session.get("user_id") if role == "user" else None,
            raised_by_agent=session.get("agent") if role == "agent" else None,
            created_at=datetime.utcnow()
        )

        db.session.add(ticket)
        db.session.commit()

        return redirect(url_for("ticket_bp.my_tickets"))

    return render_template("raise_ticket.html")


# ---------------- MY TICKETS (USER / AGENT) ----------------
@ticket_bp.route("/my-tickets")
def my_tickets():

    role = session.get("role")

    if not role:
        return redirect(url_for("user.login"))

    if role == "admin":
        return redirect(url_for("admin_bp.admin_dashboard"))

    if role == "user":
        tickets = Dispute.query.filter_by(
            raised_by_user=session.get("user_id")
        ).order_by(Dispute.created_at.desc()).all()

    elif role == "agent":
        tickets = Dispute.query.filter_by(
            raised_by_agent=session.get("agent")
        ).order_by(Dispute.created_at.desc()).all()

    else:
        tickets = []

    return render_template("my_tickets.html", tickets=tickets, role=role)


# ---------------- ADMIN: ALL TICKETS ----------------
@ticket_bp.route("/admin/tickets", methods=["GET", "POST"])
def admin_tickets():

    if session.get("role") != "admin":
        return redirect(url_for("user.login"))

    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        status    = request.form.get("status")
        note      = request.form.get("admin_note")

        ticket = Dispute.query.get(ticket_id)

        if ticket:
            ticket.status     = status
            ticket.admin_note = note

            if status == "resolved":
                ticket.resolved_at = datetime.utcnow()

            db.session.commit()

    tickets = Dispute.query.order_by(Dispute.created_at.desc()).all()

    return render_template("admin_tickets.html", tickets=tickets)