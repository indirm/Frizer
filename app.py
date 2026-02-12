from flask import session, redirect, url_for
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# --- Flask-Mail setup ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'
mail = Mail(app)

# --- App config ---
app.secret_key = "LeonInMihaFrizerja"
ADMIN_PASSWORD = "leonmiha123"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Models ---
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)

class WorkHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_hour = db.Column(db.Integer, default=8)  # 8 AM
    end_hour = db.Column(db.Integer, default=18)   # 6 PM

# --- Admin login ---
@app.route("/LeHa", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form["password"]
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("login.html")

# --- Home page ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Admin dashboard ---
@app.route("/dashboard")
def admin():
    if not session.get("admin"):
        return redirect("/LeHa")
    
    appointments = Appointment.query.order_by(Appointment.date, Appointment.time).all()
    work_hours = WorkHours.query.first() or WorkHours()
    
    return render_template("admin.html", appointments=appointments, work_hours=work_hours)

# --- Logout ---
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# --- Booking route ---
@app.route("/book", methods=["POST"])
def book():
    try:
        data = request.json

        # Get dynamic work hours
        work = WorkHours.query.first()
        WORK_START = work.start_hour if work else 8
        WORK_END = work.end_hour if work else 18

        hour = int(data["time"].split(":")[0])

        # Check working hours
        if hour < WORK_START or hour >= WORK_END:
            return jsonify({"message": f"Outside working hours ({WORK_START}:00-{WORK_END}:00)"}), 400

        # Prevent double booking
        existing = Appointment.query.filter_by(
            date=data["date"],
            time=data["time"]
        ).first()
        if existing:
            return jsonify({"message": "Time already taken"}), 400

        # Create pending appointment
        new_appointment = Appointment(
            name=data["name"],
            phone=data["phone"],
            date=data["date"],
            time=data["time"],
            approved=False
        )
        db.session.add(new_appointment)
        db.session.commit()

        # Optional: Send email to customer if you have email field
        # msg = Message("Appointment Request Received", sender="your_email@gmail.com",
        #               recipients=[data["email"]])
        # msg.body = f"Hi {data['name']}, your appointment request on {data['date']} at {data['time']} is received. Awaiting admin approval."
        # mail.send(msg)

        return jsonify({"message": "Appointment request sent! Awaiting admin approval."}), 200

    except Exception as e:
        print("Booking error:", e)
        return jsonify({"message": "Server error, try again."}), 500

# --- Approve / Reject ---
@app.route("/approve/<int:id>")
def approve(id):
    appt = Appointment.query.get(id)
    if appt:
        appt.approved = True
        db.session.commit()
        # Optional: send confirmation email here
    return redirect("/dashboard")

@app.route("/reject/<int:id>")
def reject(id):
    appt = Appointment.query.get(id)
    if appt:
        db.session.delete(appt)
        db.session.commit()
    return redirect("/dashboard")

# --- Set working hours ---
@app.route("/set_hours", methods=["POST"])
def set_hours():
    if not session.get("admin"):
        return redirect("/LeHa")

    start = int(request.form["start"])
    end = int(request.form["end"])

    work = WorkHours.query.first()
    if not work:
        work = WorkHours(start_hour=start, end_hour=end)
        db.session.add(work)
    else:
        work.start_hour = start
        work.end_hour = end

    db.session.commit()
    return redirect("/dashboard")

# --- Initialize DB ---
with app.app_context():
    db.create_all()
    # ensure default work hours exist
    if not WorkHours.query.first():
        db.session.add(WorkHours(start_hour=8, end_hour=18))
        db.session.commit()

# --- Run app ---
if __name__ == "__main__":
    app.run(debug=True)
