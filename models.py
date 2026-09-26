from sqlalchemy import Column, Integer, String, ForeignKey, Text
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description_text = Column(Text)


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    filename = Column(String)
    extracted_text = Column(Text)
    match_score = Column(Integer, default=0)
    matched_skills = Column(Text, default="")
    missing_skills = Column(Text, default="")

class ShowcaseResume(Base):
    __tablename__ = "showcase_resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    description = Column(String, default="")
    role = Column(String, default="")
    uploaded_by = Column(Integer, ForeignKey("users.id"))