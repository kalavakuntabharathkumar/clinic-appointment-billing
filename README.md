# Clinic Appointment & Billing System

A full-stack clinic workflow demo using Next.js, Bootstrap, Python Flask, PostgreSQL, Docker, and Render-friendly configuration.

## Features
- Appointment booking and status tracking
- Patient and clinician directory
- Service catalogue and invoices
- PostgreSQL schema with foreign keys and indexes
- Flask JSON API consumed by a responsive Next.js interface
- Docker Compose for local PostgreSQL + API

## Run locally (Windows-friendly)
Requirements: Node.js 20+, Python 3.11+, Docker Desktop (or a local PostgreSQL instance).

### 1. Start PostgreSQL and Flask API
From the project root:
```bash
docker compose up --build
```
The API is available at `http://localhost:5000`; health check: `/api/health`.
If you prefer not to use Docker, create a PostgreSQL database and configure `server/.env` using `server/.env.example`, then:
```powershell
cd server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### 2. Start the Next.js frontend
In another terminal:
```bash
cd client
npm install
npm run dev
```
Open `http://localhost:3000`.

### Seed data
The API automatically creates tables and inserts demo clinicians/services on first startup. Demo patient: use the booking form to create an appointment. The app is a portfolio starter; before real clinical use, add authentication/authorization, privacy controls, audit logs, migrations, backups, and appropriate healthcare compliance reviews.
