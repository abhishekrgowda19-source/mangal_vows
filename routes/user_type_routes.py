from flask import Blueprint, session, redirect, url_for, request

user_type_bp = Blueprint("user_type_bp", __name__)

@user_type_bp.route("/select-user-type", methods=["POST"])
def select_user_type():

    selected_type = request.form.get("user_type")

    if selected_type not in ["personal", "commercial"]:
        return redirect(url_for("user.login"))

    session["selected_user_type"] = selected_type

    # ✅ Personal → register
    if selected_type == "personal":
        return redirect(url_for("user.self_register"))

    # ✅ Commercial → login page (same UI, but mode is commercial)
    return redirect(url_for("user.login"))