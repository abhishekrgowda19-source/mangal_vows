from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Agent, Admin, Payment, Dispute
from database import db
from datetime import datetime, timedelta

admin_bp = Blueprint("admin_bp", __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("admin_bp.admin_login"))
        return f(*args, **kwargs)
    return decorated


# ── Login ─────────────────────────────────────────────

@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        admin    = Admin.query.filter_by(username=username).first()
        from app import bcrypt
        if not admin or not bcrypt.check_password_hash(admin.password_hash, password):
            return render_template("login.html", error="Invalid admin credentials")
        session["admin"] = admin.username
        session["role"]  = "admin"
        return redirect(url_for("admin_bp.admin_dashboard"))
    return render_template("login.html")


# ── Main Dashboard ────────────────────────────────────

@admin_bp.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    total_users     = User.query.count()
    total_agents    = Agent.query.count()
    active_subs     = User.query.filter_by(subscription_active=True).count()
    total_revenue   = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    total_revenue   = total_revenue // 100

    recent_users    = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    open_disputes   = Dispute.query.filter_by(status="open").count()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_agents=total_agents,
        active_subs=active_subs,
        total_revenue=total_revenue,
        recent_users=recent_users,
        recent_payments=recent_payments,
        open_disputes=open_disputes
    )


# ── User Management ───────────────────────────────────

@admin_bp.route("/admin-users")
@admin_required
def admin_users():
    search = request.args.get("search", "")
    query  = User.query
    if search:
        query = query.filter(
            User.name.ilike(f"%{search}%") |
            User.phone.ilike(f"%{search}%") |
            User.caste.ilike(f"%{search}%")
        )
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users, search=search)


@admin_bp.route("/admin-toggle-subscription/<user_id>")
@admin_required
def toggle_subscription(user_id):
    user = User.query.get(user_id)
    if user:
        if user.subscription_active:
            user.subscription_active = False
            user.subscription_expiry = None
        else:
            user.subscription_active = True
            user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        db.session.commit()
    return redirect(url_for("admin_bp.admin_users"))


# ── Agent Management ──────────────────────────────────

@admin_bp.route("/admin-agents")
@admin_required
def admin_agents():
    agents = Agent.query.order_by(Agent.created_at.desc()).all()
    return render_template("admin_agents.html", agents=agents)


@admin_bp.route("/admin-toggle-agent/<agent_id>")
@admin_required
def toggle_agent(agent_id):
    agent = Agent.query.get(agent_id)
    if agent:
        agent.is_active = not agent.is_active
        db.session.commit()
    return redirect(url_for("admin_bp.admin_agents"))


@admin_bp.route("/admin-kyc/<agent_id>/<action>")
@admin_required
def agent_kyc(agent_id, action):
    agent = Agent.query.get(agent_id)
    if agent and action in ["approve", "reject"]:
        agent.kyc_status = "approved" if action == "approve" else "rejected"
        db.session.commit()
    return redirect(url_for("admin_bp.admin_agents"))


# ── Payment Management ────────────────────────────────

@admin_bp.route("/admin-payments")
@admin_required
def admin_payments():
    payments           = Payment.query.order_by(Payment.created_at.desc()).all()
    total_revenue      = sum(p.amount for p in payments) // 100
    activation_revenue = sum(p.amount for p in payments if p.payment_type == "activation") // 100
    renewal_revenue    = sum(p.amount for p in payments if p.payment_type == "renewal") // 100
    return render_template(
        "admin_payments.html",
        payments=payments,
        total_revenue=total_revenue,
        activation_revenue=activation_revenue,
        renewal_revenue=renewal_revenue
    )


# ── Dispute Management ────────────────────────────────

@admin_bp.route("/admin-disputes")
@admin_required
def admin_disputes():
    status   = request.args.get("status", "open")
    type_filter = request.args.get("type", "")

    query = Dispute.query.filter_by(status=status)

    # ✅ Filter by ticket type if provided
    if type_filter:
        query = query.filter_by(ticket_type=type_filter)

    disputes = query.order_by(Dispute.created_at.desc()).all()

    # ✅ Count by type for admin overview
    open_count     = Dispute.query.filter_by(status="open").count()
    payment_count  = Dispute.query.filter_by(status="open", ticket_type="payment_issue").count()
    sub_count      = Dispute.query.filter_by(status="open", ticket_type="subscription_issue").count()
    profile_count  = Dispute.query.filter_by(status="open", ticket_type="profile_report").count()
    general_count  = Dispute.query.filter_by(status="open", ticket_type="other").count()

    return render_template(
        "admin_disputes.html",
        disputes=disputes,
        status=status,
        type_filter=type_filter,
        open_count=open_count,
        payment_count=payment_count,
        sub_count=sub_count,
        profile_count=profile_count,
        general_count=general_count
    )


@admin_bp.route("/admin-resolve-dispute/<dispute_id>", methods=["POST"])
@admin_required
def resolve_dispute(dispute_id):
    dispute = Dispute.query.get(dispute_id)
    if dispute:
        dispute.status      = request.form.get("status", "resolved")
        dispute.admin_note  = request.form.get("admin_note", "")
        dispute.resolved_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for("admin_bp.admin_disputes"))


# ── Logout ────────────────────────────────────────────

@admin_bp.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("user.home"))