"""
database/db_connection.py
--------------------------
Handles PostgreSQL connection using SQLAlchemy.
Provides session management and base ORM model.
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric,
    Date, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from contextlib import contextmanager
import streamlit as st

# Load environment variables if running locally (ignored by Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Connection string ──────────────────────────────────────────────────────────
# Try Streamlit Cloud secrets first, fallback to local .env
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except (FileNotFoundError, KeyError):
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:rc%401710@localhost:5432/placement_db")

# ── SQLAlchemy engine & session ────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ─────────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    student_id      = Column(Integer, primary_key=True, index=True)
    student_code    = Column(String(20), unique=True, nullable=False)
    name            = Column(String(100), nullable=False)
    branch          = Column(String(100), nullable=False)
    cgpa            = Column(Numeric(4, 2))
    graduation_year = Column(Integer, nullable=False)
    email           = Column(String(150), unique=True, nullable=False)
    phone           = Column(String(15))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    skills      = relationship("Skill",     back_populates="student", uselist=False, cascade="all, delete")
    placements  = relationship("Placement", back_populates="student", cascade="all, delete")


class Skill(Base):
    __tablename__ = "skills"

    skill_id            = Column(Integer, primary_key=True, index=True)
    student_id          = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), unique=True)
    python_score        = Column(Integer, default=0)
    java_score          = Column(Integer, default=0)
    sql_score           = Column(Integer, default=0)
    html_css_score      = Column(Integer, default=0)
    javascript_score    = Column(Integer, default=0)
    aptitude_score      = Column(Numeric(5, 2))
    communication_score = Column(Numeric(5, 2))
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="skills")


class Company(Base):
    __tablename__ = "companies"

    company_id   = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(150), unique=True, nullable=False)
    industry     = Column(String(100))
    location     = Column(String(100))
    website      = Column(String(200))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    placements = relationship("Placement", back_populates="company")


class Placement(Base):
    __tablename__ = "placements"

    placement_id      = Column(Integer, primary_key=True, index=True)
    student_id        = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    company_id        = Column(Integer, ForeignKey("companies.company_id", ondelete="SET NULL"), nullable=True)
    package_offered   = Column(Numeric(10, 2))
    placement_status  = Column(String(20), default="Not Placed")
    interview_date    = Column(Date)
    selection_result  = Column(String(20), default="Pending")
    offer_letter_date = Column(Date)
    notes             = Column(Text)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student",  back_populates="placements")
    company = relationship("Company",  back_populates="placements")


# ── Helpers ────────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Yield a database session and ensure it's closed after use."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """Return a raw session (caller must close it)."""
    return SessionLocal()