# EduPulse — Student Course Feedback Analysis System

EduPulse now has a public homepage, a student dashboard, and a separate authenticated administrator portal. The existing navy/purple dashboard styling and chart palette are retained.

## What's included

- Public Home, About, Contact, Student Login and Admin Login navigation.
- Student login opens directly at the student dashboard.
- Student accounts are created on first sign-in and then require the same ID, password, branch and semester on later sign-ins.
- B.Tech branches: CSE, ECE, EEE, Mechanical, Civil, IT, AI & ML, and Data Science.
- Eight semesters for every branch, with a starter branch-specific subject catalogue.
- Student pages and APIs only expose the subjects and aggregate feedback for the signed-in student's branch and semester.
- Separate admin portal with protected APIs to review individual feedback, student IDs, ratings, comments, subject and lecturer details.
- Admin can add, edit and remove subjects, update lecturer names and lecture details, and export detailed feedback to CSV.
- One feedback submission per student per subject; five required ratings and an optional 500-character comment.
- Existing PostgreSQL/Supabase storage remains supported. New columns are added with `IF NOT EXISTS`; local development uses JSON files in `data/`.

## Run locally (Windows)

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Administrator credentials

For a local demonstration, the default administrator login is:

- Login ID: `admin`
- Password: `Admin@12345`

**Change these before deployment.** Configure environment variables rather than editing source code:

```powershell
$env:ADMIN_LOGIN_ID="your-admin-id"
$env:ADMIN_PASSWORD="use-a-long-unique-password"
$env:SECRET_KEY="a-long-random-secret-value"
python app.py
```

Set the same variables in your hosting provider's server-side environment settings. Never commit real credentials or `SECRET_KEY` to source control. Use HTTPS in production.

## Student accounts

A first-time student enters a student ID, password, branch and semester on the Student Login page; this creates a local account. On subsequent visits, all four values must match. Student accounts are stored as password hashes in `data/students.json`.

This starter project does not connect to a college identity provider or verify student IDs against an official enrollment database. For a real institutional rollout, connect student login to your college SSO or import verified student accounts. Until then, first-time self-registration is suitable only for a controlled demo.

## Database configuration

Without `DATABASE_URL`, local development stores data in `data/feedback.json`, `data/students.json`, and `data/academic.json`.

For Supabase/PostgreSQL, set `DATABASE_URL` (or `POSTGRES_URL`) to the PostgreSQL connection string. Feedback submissions are stored in `course_feedback_submissions`; the app creates the table if needed and adds student/academic metadata columns without dropping existing data. Student accounts and the editable subject catalogue remain in the local JSON files, so use persistent storage or move those records to database tables before deploying to ephemeral/serverless hosting.

## Routes and access control

- `/` — public homepage
- `/student/login` — student sign-in / first-time registration
- `/student/dashboard` — student-only dashboard
- `/admin/login` — administrator sign-in
- `/admin` — admin-only management portal
- `/api/feedback` and `/api/student/*` — student-authenticated endpoints
- `/api/admin/*` — administrator-authenticated endpoints
- `/logout` — clear current session

Raw feedback records and detailed CSV export are served only by admin-protected routes. Student endpoints return only branch/semester-scoped aggregate metrics and their assigned subject catalogue.

## Important production hardening

Before using this with real student information, deploy behind HTTPS, set strong `SECRET_KEY` and administrator credentials, use persistent storage for `students.json` and `academic.json` or migrate them into PostgreSQL, add college-approved student identity verification, and configure backups and access monitoring. The demo's student self-registration is not proof of enrollment.
