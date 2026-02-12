from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    appointments = Appointment.query.order_by(Appointment.date, Appointment.time).all()
    return render_template("admin.html", appointments=appointments)

@app.route("/book", methods=["POST"])
def book():
    data = request.json

    new_appointment = Appointment(
        name=data["name"],
        phone=data["phone"],
        date=data["date"],
        time=data["time"]
    )

    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message": "Booked!"})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

