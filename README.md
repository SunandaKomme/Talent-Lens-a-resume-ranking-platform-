# TalentLens 🔍

**TalentLens** is a full-stack resume screening platform that helps recruiters instantly rank candidates against a job description — using a hybrid keyword + AI semantic matching engine — while also letting users share and browse sample resumes for different professional roles.

## Features

### Core Screening Tool
- Secure user registration & login (bcrypt-hashed passwords)
- Paste a job description and upload multiple resumes (PDF/DOCX) at once
- Automatic text extraction from uploaded resumes
- Hybrid NLP-based matching engine — combines keyword overlap with semantic similarity (Sentence-BERT embeddings) for more accurate, human-like scoring
- Ranked results showing match score, matched skills, and missing skills per candidate
- Personal screening history ("My Uploads") to revisit past job descriptions and rankings

### Resume Showcase (Community Feature)
- Users can share resumes that worked for them, tagged by role
- Searchable public showcase of sample resumes by role
- "My Contributions" page to manage resumes you've personally shared
- Secure, ownership-verified delete (users can only delete their own uploads — protected against unauthorized access on the backend, not just hidden in the UI)

### UX Details
- Consistent branded UI across all pages
- Custom in-app confirmation modals (no native browser popups)
- Profile menu with initials avatar and logout
- Responsive card-based layouts

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | HTML, CSS, vanilla JavaScript |
| Authentication | Passlib (bcrypt password hashing) |
| Resume Parsing | pdfplumber, python-docx |
| Matching Engine | Sentence-Transformers (Sentence-BERT) |
| Server | Uvicorn (ASGI) |

## Architecture

Browser (HTML/CSS/JS)
│
▼
FastAPI Backend ──────► SQLite Database
│ (Users, Jobs, Resumes,
│ ShowcaseResumes)
▼
Matching Engine
(skills_list.py + matcher.py)


## Matching Algorithm

Each candidate's score is a weighted blend of two signals:

- **60% Keyword Matching** — checks for exact skill mentions from a predefined skills list, shared between the job description and resume
- **40% Semantic Similarity** — uses a pretrained sentence embedding model (`all-MiniLM-L6-v2`) to measure how closely the overall meaning of the resume aligns with the job description, catching related terms that don't match exactly (e.g. "ML" and "Machine Learning")

This hybrid approach balances the explainability of keyword matching with the flexibility of true semantic understanding.

## Setup & Installation

### Prerequisites
- Python 3.11+
- pip

### Steps

```bash
# Clone the repository
git clone https://github.com/SunandaKomme/Talent-Lens-a-resume-ranking-platform-.git
cd Talent-Lens-a-resume-ranking-platform-

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install fastapi "uvicorn[standard]" sqlalchemy passlib[bcrypt] pdfplumber python-docx python-multipart sentence-transformers

# Create the database
python create_db.py

# Run the server
uvicorn main:app --reload
```

Then open your browser to:http://127.0.0.1:8000/



## Project Structure

resume-ranker/
├── static/ # Frontend pages (HTML/CSS/JS)
│ ├── index.html # Homepage
│ ├── login.html
│ ├── register.html
│ ├── forgot_password.html
│ ├── dashboard.html # Screen Candidates (core tool)
│ ├── my_uploads.html # Screening history
│ ├── showcase_upload.html # Contribute a resume
│ ├── showcase_view.html # Sample Resumes (browse/search)
│ ├── my_contributions.html
│ └── style.css
├── main.py # FastAPI app & all API routes
├── database.py # Database connection setup
├── models.py # SQLAlchemy table definitions
├── matcher.py # Hybrid matching engine
├── skills_list.py # Predefined skill keywords
├── create_db.py # Database initialization script
└── requirements # (see Setup section above)


## Security Notes

- Passwords are hashed with bcrypt — never stored in plain text
- All delete operations are protected by ownership checks on the backend, preventing unauthorized users from deleting others' data (fixes a Broken Access Control / IDOR vulnerability identified and resolved during development)

## Known Limitations

- Password reset is simplified (no email verification link) — suitable for demo purposes, not production
- Browsers cannot preview `.docx` files inline, so these open/download rather than displaying in-browser (a genuine browser limitation, not an app bug)
- Currently runs locally; not yet deployed to a live server

## Author

Built by Sunanda Komme as a major project 