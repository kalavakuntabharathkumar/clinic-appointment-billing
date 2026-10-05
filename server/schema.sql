CREATE TABLE IF NOT EXISTS patients (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  phone VARCHAR(30) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS clinicians (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  specialty VARCHAR(100) NOT NULL,
  room VARCHAR(40) NOT NULL DEFAULT 'Main clinic'
);
CREATE TABLE IF NOT EXISTS services (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
  duration_minutes INTEGER NOT NULL DEFAULT 30 CHECK (duration_minutes > 0)
);
CREATE TABLE IF NOT EXISTS appointments (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
  clinician_id INTEGER NOT NULL REFERENCES clinicians(id) ON DELETE RESTRICT,
  service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'booked' CHECK (status IN ('booked','confirmed','completed','cancelled')),
  notes TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (clinician_id, appointment_date, appointment_time)
);
CREATE TABLE IF NOT EXISTS invoices (
  id SERIAL PRIMARY KEY,
  appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id) ON DELETE RESTRICT,
  amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
  status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK (status IN ('unpaid','paid','void')),
  issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date, appointment_time);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
