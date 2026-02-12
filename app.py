from flask import session, redirect, url_for
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = "LeonInMihaFrizerja"
ADMIN_PASSWORD = "leonmiha123"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route("/LeHa", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form["password"]
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("login.html")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def admin():
    if not session.get("admin"):
        return redirect("/LeHa")

    appointments = Appointment.query.order_by(Appointment.date, Appointment.time).all()
    return render_template("admin.html", appointments=appointments)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


@app.route("/book", methods=["POST"])
def book():
    data = request.json

    # 1️⃣ Check working hours
    hour = int(data["time"].split(":")[0])
    WORK_START = 14
    WORK_END = 20
    if hour < WORK_START or hour >= WORK_END:
        return jsonify({"message": f"Outside working hours ({WORK_START}:00-{WORK_END}:00)"}), 400

    # 2️⃣ Check if time slot is already taken
    existing = Appointment.query.filter_by(
        date=data["date"],
        time=data["time"],
        approved=True   # only approved appointments block the slot
    ).first()

    if existing:
        return jsonify({"message": "Time already taken"}), 400

    # 3️⃣ Create appointment (pending approval)
    new_appointment = Appointment(
        name=data["name"],
        phone=data["phone"],
        date=data["date"],
        time=data["time"],
        approved=False
    )

    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message": "Appointment request sent. Awaiting admin approval!"})

@app.route("/approve/<int:id>")
def approve(id):
    appt = Appointment.query.get(id)
    appt.approved = True
    db.session.commit()
    return redirect("/dashboard")


with app.app_context():
    db.create_all()
approved = db.Column(db.Boolean, default=False)
if __name__ == "__main__":
    app.run(debug=True)

