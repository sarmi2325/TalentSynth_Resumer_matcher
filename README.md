# Resume Matcher - AI-Powered Resume Analysis


---
## Demo

Try out the live demo of the project here:  
[TalentSynth Resume Matcher](https://talentsynthresumermatcher-production.up.railway.app/)

This is a Django application that uses cutting-edge AI to parse resumes, extract structured data, and match them against job descriptions with unmatched precision.

---

## What This Application Does

- Resume Parsing: Uses LlamaParse and Google Gemini AI to extract structured data from PDF/DOC resumes.
- Job Matching: AI-powered comparison of resumes against job descriptions for precise compatibility scoring.
- User Management: Full authentication system with user profiles and secure session management.
- Real-time Analysis: Instant AI-driven feedback on resume-job fit.
- Data Storage: Uses structured JSON to store detailed resume components.

---

## Tech Stack

- Backend: Django 5.2.7
- AI Engine: LlamaParse + Google Gemini 2.5 Flash
- Database: SQLite (development) / PostgreSQL (production)
- Auth: Django Allauth for Google OAuth
- File Processing: PyMuPDF, python-docx
- Production: Gunicorn, deployed on Railway

---
# Similarity Scoring Strategy

This document outlines the methodology for evaluating resume-job description similarity based on categorized skills and experiences.

---

## Skill Match Categories

Each skill in a resume is categorized into one of four main types:

### Technical Skills
- **Examples:** Python, JavaScript, React, SQL, Machine Learning, AWS  
- **What it measures:** Programming languages, frameworks, tools, technologies  
- **Evidence:** Projects, certifications, work experience using these skills  

### Soft Skills
- **Examples:** Leadership, Communication, Teamwork, Problem-solving, Time Management  
- **What it measures:** Interpersonal skills and behavioral competencies  
- **Evidence:** Leadership roles, team projects, volunteer work, achievements  

### Experience
- **Examples:** Years of experience, Industry experience, Project management, Team leadership  
- **What it measures:** Professional experience relevant to the job  
- **Evidence:** Work history, project duration, team size, responsibilities  

### Education
- **Examples:** Degree level, Relevant coursework, Academic projects, GPA  
- **What it measures:** Educational background and academic achievements  
- **Evidence:** Degrees, certifications, academic projects, relevant coursework  

---

## Scoring System

Each skill receives a score between **0-2**:

- **0 = Not Mentioned** → Skill not found in resume  
- **1 = Mentioned but Weak Evidence** → Listed but no projects/impact shown  
- **2 = Strong Evidence** → Projects, experience, measurable outcomes  

---

## Analysis Breakdown

The report generates **4 category scores**:
- Technical Skills Score  
- Soft Skills Score  
- Experience Score  
- Education Score  

---

## Overall Recommendation Levels

The overall fit percentage is translated into four recommendation levels:

- **Strong Match** → 80% and above  
- **Good Match** → 60–79%  
- **Moderate Match** → 40–59%  
- **Weak Match** → Below 40%  

## Installation Guide

1. Clone the repo:
git clone <your-repo-url>
cd resume

text

2. Create virtual environment:
python -m venv venv
source venv/bin/activate # Linux/macOS
venv\Scripts\activate # Windows

text

3. Install dependencies:
pip install -r requirements.txt

text

4. Configure environment variables in `.env`:
LLAMA_API_KEY=your_llama_parse_api_key
GEMINI_API_KEY=your_google_gemini_api_key
SECRET_KEY=your_django_secret_key
DEBUG=True

text

5. Database setup:
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

text

6. Run server:
python manage.py runserver

text

Visit `http://127.0.0.1:8000` to get started.

---

## Project Structure Overview

resume_matcher/
├── accounts/ # User and resume logic
│ ├── models.py # UserProfile, ResumeAnalysis
│ ├── views.py # Core logic and endpoints
│ ├── resume_parser.py # AI parsing integration
│ └── templates/ # HTML/UI templates
├── resumes/ # File upload handling
├── media/ # Uploaded files storage
├── db.sqlite3 # Database file (dev)
└── requirements.txt # Dependencies

text

---

## Key Features

### Resume Parsing
- Extracts text and data using LlamaParse and Gemini AI.
- Calculates experience and identifies skills automatically.

### Job Matching
- AI-powered resume to job description scoring.
- Provides detailed strengths, weakness analysis, and recommendations.

### User Management
- Secure login/signup with Django Allauth.
- User profiles with uploaded resumes and analysis data.

---

## API Endpoints (Sample)

- `GET /accounts/login/` - User login page
- `GET /accounts/signup/` - User registration page
- `POST /accounts/logout/` - Logout user
- `GET /profile/` - Upload resume
- `GET /dashboard/` - View match results and analysis
- `POST /upload-resume/` - Upload resume endpoint
- `POST /analyze/` - Analyze job description

---

## Development Commands

- Migrate DB:  
python manage.py makemigrations
python manage.py migrate

text

- Run tests:  
python manage.py test

text

- Production deployment:  
pip install gunicorn
gunicorn resume_matcher.wsgi:application

text

---





