# Smart Resume Analyser

An AI-assisted resume scoring, feedback, and job-matching platform. Upload a
resume as a PDF or a scanned image and get back a scored, section-by-section
breakdown — skills, education, experience, and formatting — plus an
ATS-compatibility check and concrete suggestions for improvement.

## Features

- **OCR + PDF text extraction** (PyMuPDF for native PDFs, Tesseract for
  scanned images) so both formats work through the same pipeline
- **NLP-driven skill extraction and section scoring** — NLTK tokenisation,
  stopword filtering, and tagging against a curated skills taxonomy
- **ATS-compatibility simulation** with a transparent, explainable scoring
  breakdown rather than a single opaque number
- **Job-description matching** — paste a job description and see how well a
  given resume fits it
- **Personalised feedback generation** based on career goal, experience
  level, and target role
- **Guided resume builder** with multiple templates
- **Auth system** with email-based password reset (Flask-Mail) and a
  per-user resume history
- **Analytics dashboard** — score distribution, top skills, career-field
  breakdown across every resume analysed so far, with CSV/JSON export for
  further analysis (e.g. Power BI)

## Stack

Python · Flask · SQL Server (`pyodbc`) · NLTK · PyMuPDF · Tesseract OCR
(`pytesseract`) · Flask-Mail · HTML/CSS/JS

## Project layout

```
app.py              Flask routes (auth, upload, dashboard, builder, job match)
analyzer.py         Resume parsing, scoring, ATS simulation, feedback generation
models.py           Database access layer (resumes, skills, users, auth)
config.py           App configuration (DB, mail, upload limits) via env vars
nlp/                Skill extraction
templates/          Jinja2 templates
static/             CSS, JS, uploaded files
setup_db.sql        Core schema (resumes, skills, education, experience)
setup_users_table.sql   Auth-related schema (users, password reset codes)
```

## Run it

Requires Python 3, a Microsoft SQL Server instance, and Tesseract OCR
installed locally (used for scanned-image resumes).

```bash
python -m venv venv
venv\Scripts\activate        # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Set up the database (SSMS or `sqlcmd`):

```bash
sqlcmd -S localhost -i setup_db.sql
sqlcmd -S localhost -i setup_users_table.sql
```

Configure via environment variables (all have local-dev defaults in
`config.py`): `SQL_SERVER`, `SQL_DATABASE`, `SQL_DRIVER`, `SQL_TRUSTED_CONNECTION`
(or `SQL_USERNAME`/`SQL_PASSWORD`), `MAIL_SERVER`, `MAIL_USERNAME`,
`MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` (for password-reset emails), and
`SECRET_KEY`.

```bash
python app.py
```

## Routes

| Path | Description |
|---|---|
| `/register`, `/login`, `/logout` | Account creation and session auth |
| `/forgot-password`, `/verify-code`, `/reset-password` | Email-based password reset |
| `/` | Upload a resume |
| `/result/<id>` | Scored breakdown for a given resume |
| `/personalize/<id>` | Personalised feedback for a given resume |
| `/job-match/<id>` | Match a resume against a pasted job description |
| `/builder`, `/builder/<template>` | Guided resume builder |
| `/history` | A user's past resume analyses |
| `/dashboard`, `/api/dashboard-data` | Analytics dashboard |
| `/export/csv` | CSV export of dashboard data |
