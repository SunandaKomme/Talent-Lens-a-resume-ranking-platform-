from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from matcher import match_resume_to_job

from database import SessionLocal
from models import User
from fastapi import UploadFile, File, Form
from typing import List
import pdfplumber
import docx
from models import Job, Resume, ShowcaseResume

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def homepage():
    return FileResponse("static/index.html")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register(name: str, email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(password)
    new_user = User(name=name, email=email, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully!", "user_id": new_user.id}
@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return{"message": "Login successful!", "user_id": user.id, "name": user.name}

def extract_text(file: UploadFile):
    if file.filename.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    elif file.filename.endswith(".docx"):
        doc = docx.Document(file.file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    else:
        return ""


@app.post("/upload-job")
def upload_job(
    user_id: int = Form(...),
    description_text: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    new_job = Job(user_id=user_id, description_text=description_text)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    for resume_file in resumes:
        text = extract_text(resume_file)
        new_resume = Resume(
            job_id=new_job.id,
            filename=resume_file.filename,
            extracted_text=text
        )
        db.add(new_resume)

    db.commit()

    return {"message": "Job and resumes uploaded successfully!", "job_id": new_job.id}

@app.post("/rank/{job_id}")
def rank_resumes(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()

    for resume in resumes:
        result = match_resume_to_job(job.description_text, resume.extracted_text)
        resume.match_score = result["score"]
        resume.matched_skills = ", ".join(result["matched_skills"])
        resume.missing_skills = ", ".join(result["missing_skills"])

    db.commit()

    resumes_sorted = sorted(resumes, key=lambda r: r.match_score, reverse=True)

    return [
        {
            "filename": r.filename,
            "score": r.match_score,
            "matched_skills": r.matched_skills,
            "missing_skills": r.missing_skills
        }
        for r in resumes_sorted
    ]

@app.post("/showcase/upload")
def upload_showcase_resume(
    user_id: int = Form(...),
    description: str = Form(""),
    role: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    import shutil
    import os

    os.makedirs("static/showcase_files", exist_ok=True)
    file_path = f"static/showcase_files/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_showcase = ShowcaseResume(
        filename=file.filename,
        description=description,
        role=role,
        uploaded_by=user_id
    )
    db.add(new_showcase)
    db.commit()
    db.refresh(new_showcase)

    return {"message": "Resume shared successfully!", "id": new_showcase.id}
    
@app.get("/showcase/list")
def list_showcase_resumes(db: Session = Depends(get_db)):
    resumes = db.query(ShowcaseResume).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "description": r.description,
            "role": r.role,
            "uploaded_by": r.uploaded_by,
            "file_url": f"/static/showcase_files/{r.filename}"
        }
        for r in resumes
    ]


@app.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email")
    return {"message": "Email verified. You can now reset your password."}


@app.post("/reset-password")
def reset_password(email: str, new_password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email")
    user.hashed_password = pwd_context.hash(new_password)
    db.commit()
    return {"message": "Password reset successful! You can now log in."}

@app.delete("/showcase/delete/{resume_id}")
def delete_showcase_resume(resume_id: int, user_id: int, db: Session = Depends(get_db)):
    import os

    resume = db.query(ShowcaseResume).filter(ShowcaseResume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume.uploaded_by != user_id:
        raise HTTPException(status_code=403, detail="You can only delete resumes you uploaded")

    file_path = f"static/showcase_files/{resume.filename}"
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(resume)
    db.commit()

    return {"message": "Resume deleted successfully"}

@app.get("/my-uploads/{user_id}")
def get_my_uploads(user_id: int, db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.id.desc()).all()

    result = []
    for job in jobs:
        resumes = db.query(Resume).filter(Resume.job_id == job.id).all()
        resumes_sorted = sorted(resumes, key=lambda r: r.match_score, reverse=True)

        result.append({
            "job_id": job.id,
            "description_text": job.description_text,
            "resumes": [
                {
                    "filename": r.filename,
                    "score": r.match_score,
                    "matched_skills": r.matched_skills,
                    "missing_skills": r.missing_skills
                }
                for r in resumes_sorted
            ]
        })

    return result


@app.get("/my-contributions/{user_id}")
def get_my_contributions(user_id: int, db: Session = Depends(get_db)):
    resumes = db.query(ShowcaseResume).filter(ShowcaseResume.uploaded_by == user_id).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "description": r.description,
            "role": r.role,
            "file_url": f"/static/showcase_files/{r.filename}"
        }
        for r in resumes
    ]


@app.delete("/job/delete/{job_id}")
def delete_job(job_id: int, user_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own job entries")

    db.query(Resume).filter(Resume.job_id == job_id).delete()
    db.delete(job)
    db.commit()

    return {"message": "Job and its resumes deleted successfully"}