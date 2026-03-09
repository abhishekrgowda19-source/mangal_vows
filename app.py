from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mangal_secret_key")

USERS_FILE = "users.json"


# ---------- Utility Functions ----------

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)


def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))[-10:]


def normalize_time(t):
    t = t.strip()
    if len(t) > 5:
        return t[:5]
    return t


# ---------- Routes ----------

@app.route("/")
def home():
    return render_template("login.html")


# ---------- Commercial Login ----------

@app.route("/login", methods=["POST"])
def login():

    name3 = request.form["name3"].strip().upper()
    birthtime = normalize_time(request.form["birthtime"])
    birthplace = request.form["birthplace"].strip().lower()
    phone = normalize_phone(request.form["phone"])

    users = load_users()

    for user in users:

        user_phone = normalize_phone(user.get("phone", ""))
        user_time = normalize_time(user.get("birthtime", ""))
        user_place = user.get("birthplace", "").lower()

        if (
            user.get("name3", "").upper() == name3
            and user_time == birthtime
            and user_place == birthplace
            and user_phone == phone
        ):

            session["user"] = user_phone

            if user.get("subscription_active", False):
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("subscribe"))

    return "Invalid Commercial Credentials"


# ---------- Personal Login (Direct Dashboard) ----------

@app.route("/personal_login", methods=["POST"])
def personal_login():

    fullname = request.form["fullname"]
    email = request.form["email"]
    phone = normalize_phone(request.form["phone"])

    session["user"] = phone

    return redirect(url_for("dashboard"))


# ---------- Subscription Page ----------

@app.route("/subscribe")
def subscribe():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template("subscribe.html")


# ---------- Activate Subscription ----------

@app.route("/activate", methods=["POST"])
def activate():

    if "user" not in session:
        return redirect(url_for("home"))

    users = load_users()

    for user in users:
        if normalize_phone(user.get("phone", "")) == session["user"]:
            user["subscription_active"] = True
            break

    save_users(users)

    return redirect(url_for("dashboard"))


# ---------- Dashboard ----------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template("dashboard.html")


# ---------- Logout ----------

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("home"))


# ---------- Run Server ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)