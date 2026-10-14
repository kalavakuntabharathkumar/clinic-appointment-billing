# Clinic API reference

Base URL: `http://localhost:5000/api`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/clinicians` | List clinicians |
| GET | `/services` | List consultation services |
| GET | `/appointments` | List appointments with patient/clinician/service details |
| POST | `/appointments` | Book an appointment and create invoice |
| PATCH | `/appointments/:id/status` | Update booking status |
| GET | `/invoices` | List invoices |
| PATCH | `/invoices/:id/status` | Update invoice status |

Booking requires `fullName`, `email`, `phone`, `clinicianId`, `serviceId`, `appointmentDate`, and `appointmentTime`. The database has a unique clinician/date/time constraint to prevent overlapping appointments for a clinician.
