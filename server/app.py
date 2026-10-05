import os
from datetime import date, datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()
app = Flask(__name__)
CORS(app, origins=[os.getenv("CORS_ORIGIN", "http://localhost:3000")])
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://clinic:clinic_dev_password@localhost:5432/clinicdb")

def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                  id SERIAL PRIMARY KEY, full_name VARCHAR(120) NOT NULL,
                  email VARCHAR(180) NOT NULL UNIQUE, phone VARCHAR(30) NOT NULL,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS clinicians (
                  id SERIAL PRIMARY KEY, full_name VARCHAR(120) NOT NULL,
                  specialty VARCHAR(100) NOT NULL, room VARCHAR(40) NOT NULL DEFAULT 'Main clinic'
                );
                CREATE TABLE IF NOT EXISTS services (
                  id SERIAL PRIMARY KEY, name VARCHAR(120) NOT NULL,
                  price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
                  duration_minutes INTEGER NOT NULL DEFAULT 30 CHECK (duration_minutes > 0)
                );
                CREATE TABLE IF NOT EXISTS appointments (
                  id SERIAL PRIMARY KEY,
                  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
                  clinician_id INTEGER NOT NULL REFERENCES clinicians(id) ON DELETE RESTRICT,
                  service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
                  appointment_date DATE NOT NULL, appointment_time TIME NOT NULL,
                  status VARCHAR(20) NOT NULL DEFAULT 'booked' CHECK (status IN ('booked','confirmed','completed','cancelled')),
                  notes TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  UNIQUE (clinician_id, appointment_date, appointment_time)
                );
                CREATE TABLE IF NOT EXISTS invoices (
                  id SERIAL PRIMARY KEY, appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id) ON DELETE RESTRICT,
                  amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
                  status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK (status IN ('unpaid','paid','void')),
                  issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date, appointment_time);
                CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
            """)
            cur.execute("SELECT COUNT(*) AS n FROM clinicians")
            if cur.fetchone()["n"] == 0:
                cur.executemany("INSERT INTO clinicians (full_name, specialty, room) VALUES (%s,%s,%s)", [
                    ("Dr. Maya Rao", "General Medicine", "Room 101"),
                    ("Dr. Arjun Mehta", "Dermatology", "Room 204"),
                    ("Dr. Nisha Iyer", "Pediatrics", "Room 103"),
                ])
            cur.execute("SELECT COUNT(*) AS n FROM services")
            if cur.fetchone()["n"] == 0:
                cur.executemany("INSERT INTO services (name, price, duration_minutes) VALUES (%s,%s,%s)", [
                    ("General consultation", 600, 30),
                    ("Dermatology consultation", 850, 30),
                    ("Pediatric consultation", 700, 30),
                    ("Follow-up visit", 350, 15),
                ])

def serialize(row):
    if not row: return row
    return {k: (v.isoformat() if hasattr(v, "isoformat") else float(v) if k == "price" or k == "amount" else v) for k, v in dict(row).items()}

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "clinic-api"})

@app.get("/api/clinicians")
def clinicians():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM clinicians ORDER BY full_name")
        return jsonify([serialize(r) for r in cur.fetchall()])

@app.get("/api/services")
def services():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM services ORDER BY price")
        return jsonify([serialize(r) for r in cur.fetchall()])

@app.get("/api/appointments")
def list_appointments():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.notes,
                 p.full_name AS patient_name, p.email AS patient_email, p.phone AS patient_phone,
                 c.full_name AS clinician_name, c.specialty, s.name AS service_name, s.price
          FROM appointments a JOIN patients p ON p.id=a.patient_id
          JOIN clinicians c ON c.id=a.clinician_id JOIN services s ON s.id=a.service_id
          ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT 100
        """)
        return jsonify([serialize(r) for r in cur.fetchall()])

@app.post("/api/appointments")
def create_appointment():
    data = request.get_json(silent=True) or {}
    required = ["fullName", "email", "phone", "clinicianId", "serviceId", "appointmentDate", "appointmentTime"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({"message": "Missing required fields", "fields": missing}), 400
    try:
        appt_date = date.fromisoformat(data["appointmentDate"])
        if appt_date < date.today():
            return jsonify({"message": "Appointment date cannot be in the past"}), 400
        with connect() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO patients (full_name,email,phone) VALUES (%s,%s,%s)
              ON CONFLICT (email) DO UPDATE SET full_name=EXCLUDED.full_name, phone=EXCLUDED.phone
              RETURNING id
            """, (data["fullName"].strip(), data["email"].strip().lower(), data["phone"].strip()))
            patient_id = cur.fetchone()["id"]
            cur.execute("SELECT id FROM clinicians WHERE id=%s", (data["clinicianId"],))
            if not cur.fetchone(): return jsonify({"message": "Clinician not found"}), 404
            cur.execute("SELECT id, price FROM services WHERE id=%s", (data["serviceId"],))
            service = cur.fetchone()
            if not service: return jsonify({"message": "Service not found"}), 404
            cur.execute("""
              INSERT INTO appointments (patient_id,clinician_id,service_id,appointment_date,appointment_time,notes)
              VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
            """, (patient_id, data["clinicianId"], data["serviceId"], appt_date, data["appointmentTime"], (data.get("notes") or "").strip()))
            appointment_id = cur.fetchone()["id"]
            cur.execute("INSERT INTO invoices (appointment_id,amount) VALUES (%s,%s)", (appointment_id, service["price"]))
            return jsonify({"id": appointment_id, "message": "Appointment booked", "invoiceAmount": float(service["price"])}), 201
    except psycopg.errors.UniqueViolation:
        return jsonify({"message": "This clinician already has an appointment at that date and time. Choose another slot."}), 409
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid date, time, or identifier format"}), 400

@app.patch("/api/appointments/<int:appointment_id>/status")
def update_status(appointment_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"booked", "confirmed", "completed", "cancelled"}:
        return jsonify({"message": "Status must be booked, confirmed, completed, or cancelled"}), 400
    with connect() as conn, conn.cursor() as cur:
        cur.execute("UPDATE appointments SET status=%s WHERE id=%s RETURNING id,status", (status, appointment_id))
        row = cur.fetchone()
        if not row: return jsonify({"message": "Appointment not found"}), 404
        return jsonify(row)

@app.get("/api/invoices")
def invoices():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT i.id, i.amount, i.status, i.issued_at, a.appointment_date, p.full_name AS patient_name,
                 s.name AS service_name, c.full_name AS clinician_name
          FROM invoices i JOIN appointments a ON a.id=i.appointment_id
          JOIN patients p ON p.id=a.patient_id JOIN services s ON s.id=a.service_id
          JOIN clinicians c ON c.id=a.clinician_id ORDER BY i.issued_at DESC LIMIT 100
        """)
        return jsonify([serialize(r) for r in cur.fetchall()])

@app.patch("/api/invoices/<int:invoice_id>/status")
def update_invoice(invoice_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"unpaid", "paid", "void"}:
        return jsonify({"message": "Status must be unpaid, paid, or void"}), 400
    with connect() as conn, conn.cursor() as cur:
        cur.execute("UPDATE invoices SET status=%s WHERE id=%s RETURNING id,status", (status, invoice_id))
        row = cur.fetchone()
        if not row: return jsonify({"message": "Invoice not found"}), 404
        return jsonify(row)

@app.errorhandler(500)
def internal_error(_error):
    return jsonify({"message": "Internal server error"}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
