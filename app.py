from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mangal_secret_key")


# Load users safely
def load_users():
    if not os.path.exists("users.json"):
        return []
    with open("users.json", "r") as file:
        return json.load(file)


def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    name3 = request.form["name3"].upper()
    surname3 = request.form["surname3"].upper()
    dob = request.form["dob"]
    birthtime = request.form["birthtime"]
    birthplace = request.form["birthplace"]
    phone = request.form["phone"]

    users = load_users()

    for user in users:
        if (user["name3"] == name3 and
            user["surname3"] == surname3 and
            user["dob"] == dob and
            user["birthtime"] == birthtime and
            user["birthplace"].lower() == birthplace.lower() and
            user["phone"] == phone):

            session["user"] = phone

            # Check subscription
            if user.get("subscription_active"):
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("subscribe"))

    return "Invalid Credentials"


@app.route("/subscribe")
def subscribe():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("subscribe.html")


@app.route("/activate", methods=["POST"])
def activate():

    if "user" not in session:
        return redirect(url_for("home"))

    users = load_users()

    for user in users:
        if user["phone"] == session["user"]:
            user["subscription_active"] = True
            break

    save_users(users)

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
