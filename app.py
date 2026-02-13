from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


app = Flask(__name__)

# --- Flask-Mail setup ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'
#mail = Mail(app)

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

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))      # e.g., "Haircut John"
    description = db.Column(db.String(200)) # optional
    before_image = db.Column(db.String(200)) # path to static/images/before.jpg
    after_image = db.Column(db.String(200))  # path to static/images/after.jpg

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)

@app.route("/admin/services", methods=["GET", "POST"])
def manage_services():
    if not session.get("admin"):
        return redirect("/LeHa")
    
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        service = Service(name=name, price=price)
        db.session.add(service)
        db.session.commit()
        return redirect("/admin/services")
    
    services = Service.query.all()
    return render_template("admin_services.html", services=services)


@app.route("/admin/service/delete/<int:id>")
def delete_service(id):
    if not session.get("admin"):
        return redirect("/LeHa")
    
    service = Service.query.get(id)
    if service:
        db.session.delete(service)
        db.session.commit()
    return redirect("/dashboard")


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
    return render_template("index.html", datetime=datetime)

@app.route("/admin/gallery", methods=["GET", "POST"])
def manage_gallery():
    if not session.get("admin"):
        return redirect("/LeHa")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        before = request.files["before"]
        after = request.files["after"]

        before_path = "images/" + before.filename
        after_path = "images/" + after.filename

        before.save(os.path.join("static", before_path))
        after.save(os.path.join("static", after_path))

        entry = Gallery(
            title=title,
            description=description,
            before_image=before_path,
            after_image=after_path
        )

        db.session.add(entry)
        db.session.commit()

        return redirect("/admin/gallery")

    images = Gallery.query.all()
    return render_template("admin_gallery.html", images=images)

@app.route("/admin/gallery/delete/<int:id>")
def delete_gallery(id):
    if not session.get("admin"):
        return redirect("/LeHa")

    image = Gallery.query.get(id)
    if image:
        db.session.delete(image)
        db.session.commit()

    return redirect("/admin/gallery")


# --- Admin dashboard ---
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/LeHa")

    appointments = Appointment.query.order_by(Appointment.date, Appointment.time).all()
    services = Service.query.all()
    gallery = Gallery.query.all()
    work_hours = WorkHours.query.first() or WorkHours()

    return render_template(
        "admin_dashboard.html",
        appointments=appointments,
        services=services,
        gallery=gallery,
        work_hours=work_hours
    )


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
        work = WorkHours.query.first() or WorkHours()
        start, end = work.start_hour, work.end_hour

        hour = int(data["time"].split(":")[0])
        if hour < start or hour >= end:
            return jsonify({"message": f"Outside working hours ({start}:00-{end}:00)"}), 400

        existing = Appointment.query.filter_by(date=data["date"], time=data["time"]).first()
        if existing:
            return jsonify({"message": "Time already taken"}), 400

        new_appt = Appointment(
            name=data["name"],
            phone=data["phone"],
            date=data["date"],
            time=data["time"],
            approved=False
        )
        db.session.add(new_appt)
        db.session.commit()

        return jsonify({"message": "Appointment request sent! Awaiting admin approval."})
    except Exception as e:
        print(e)
        return jsonify({"message": "Server error"}), 500

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

@app.route("/cenik")
def cenik():
    services = Service.query.all()
    return render_template("cenik.html", services=services)

@app.route("/galerija")
def galerija():
    gallery = Gallery.query.all()
    return render_template("galerija.html", gallery=gallery)

@app.route("/o_nama")
def o_nama():
    return render_template("o_nama.html")

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
