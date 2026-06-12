"""
app/utils/data_utils.py
------------------------
Helper functions for DB queries, DataFrame conversions,
and PDF/CSV report generation used across Streamlit pages.
"""

import pandas as pd
import io
from sqlalchemy import func, distinct
from database.db_connection import (
    get_db_session, Student, Skill, Placement, Company
)


# ── Generic query helpers ──────────────────────────────────────────────────────

def fetch_all_students() -> pd.DataFrame:
    """Return all students joined with their latest placement status."""
    session = get_db_session()
    try:
        rows = (
            session.query(
                Student.student_id, Student.student_code, Student.name,
                Student.branch, Student.cgpa, Student.graduation_year,
                Student.email, Student.phone,
                Placement.placement_status, Placement.package_offered,
                Company.company_name
            )
            .outerjoin(Placement, Student.student_id == Placement.student_id)
            .outerjoin(Company,   Placement.company_id == Company.company_id)
            .order_by(Student.student_id)
            .all()
        )
        cols = [
            "student_id", "student_code", "name", "branch", "cgpa",
            "graduation_year", "email", "phone",
            "placement_status", "package_offered", "company_name"
        ]
        return pd.DataFrame(rows, columns=cols)
    finally:
        session.close()


def fetch_student_with_skills(student_id: int) -> dict:
    """Return a full student profile including skills."""
    session = get_db_session()
    try:
        student  = session.query(Student).filter_by(student_id=student_id).first()
        skill    = session.query(Skill).filter_by(student_id=student_id).first()
        placement= session.query(Placement).filter_by(student_id=student_id).first()
        if not student:
            return {}
        return {
            "student":   student,
            "skill":     skill,
            "placement": placement,
        }
    finally:
        session.close()


def fetch_skills_dataframe() -> pd.DataFrame:
    """Return all skill records joined with student info."""
    session = get_db_session()
    try:
        rows = (
            session.query(
                Student.student_id, Student.name, Student.branch, Student.cgpa,
                Skill.python_score, Skill.java_score, Skill.sql_score,
                Skill.html_css_score, Skill.javascript_score,
                Skill.aptitude_score, Skill.communication_score,
                Placement.placement_status
            )
            .join(Skill,     Student.student_id == Skill.student_id)
            .outerjoin(Placement, Student.student_id == Placement.student_id)
            .all()
        )
        cols = [
            "student_id", "name", "branch", "cgpa",
            "python_score", "java_score", "sql_score",
            "html_css_score", "javascript_score",
            "aptitude_score", "communication_score",
            "placement_status"
        ]
        return pd.DataFrame(rows, columns=cols)
    finally:
        session.close()


def fetch_placements_dataframe() -> pd.DataFrame:
    """Return all placement records."""
    session = get_db_session()
    try:
        rows = (
            session.query(
                Placement.placement_id, Student.student_code, Student.name,
                Student.branch, Student.cgpa,
                Company.company_name, Placement.package_offered,
                Placement.placement_status, Placement.interview_date,
                Placement.selection_result, Placement.offer_letter_date
            )
            .join(Student,  Placement.student_id == Student.student_id)
            .outerjoin(Company, Placement.company_id == Company.company_id)
            .order_by(Placement.placement_id)
            .all()
        )
        cols = [
            "placement_id", "student_code", "name", "branch", "cgpa",
            "company_name", "package_offered", "placement_status",
            "interview_date", "selection_result", "offer_letter_date"
        ]
        return pd.DataFrame(rows, columns=cols)
    finally:
        session.close()


def fetch_companies() -> pd.DataFrame:
    """Return all companies."""
    session = get_db_session()
    try:
        rows = session.query(Company).order_by(Company.company_name).all()
        return pd.DataFrame(
            [(c.company_id, c.company_name, c.industry, c.location) for c in rows],
            columns=["company_id", "company_name", "industry", "location"]
        )
    finally:
        session.close()


# ── KPI summary ────────────────────────────────────────────────────────────────

def get_dashboard_kpis() -> dict:
    """Compute top-level KPIs for the analytics dashboard."""
    session = get_db_session()
    try:
        total_students = session.query(func.count(Student.student_id)).scalar() or 0

        placed_count = (
            session.query(func.count(Placement.placement_id))
            .filter(Placement.placement_status == "Placed")
            .scalar() or 0
        )

        avg_pkg = (
            session.query(func.avg(Placement.package_offered))
            .filter(Placement.placement_status == "Placed")
            .scalar()
        )

        max_pkg = (
            session.query(func.max(Placement.package_offered))
            .filter(Placement.placement_status == "Placed")
            .scalar()
        )

        placement_pct = round((placed_count / total_students * 100), 2) if total_students else 0

        return {
            "total_students":    total_students,
            "placed_students":   placed_count,
            "placement_pct":     placement_pct,
            "avg_package":       round(float(avg_pkg or 0), 2),
            "highest_package":   round(float(max_pkg or 0), 2),
        }
    finally:
        session.close()


def get_branch_stats() -> pd.DataFrame:
    """Branch-wise placement statistics."""
    session = get_db_session()
    try:
        rows = (
            session.query(
                Student.branch,
                func.count(distinct(Student.student_id)).label("total"),
                func.sum(
                    func.cast(Placement.placement_status == "Placed", Integer)
                ).label("placed")
            )
            .outerjoin(Placement, Student.student_id == Placement.student_id)
            .group_by(Student.branch)
            .all()
        )
        df = pd.DataFrame(rows, columns=["branch", "total", "placed"])
        df["placed"]      = df["placed"].fillna(0).astype(int)
        df["not_placed"]  = df["total"] - df["placed"]
        df["pct_placed"]  = (df["placed"] / df["total"] * 100).round(2)
        return df
    finally:
        session.close()


def get_company_hiring_stats() -> pd.DataFrame:
    """Company-wise placement counts and average package."""
    session = get_db_session()
    try:
        rows = (
            session.query(
                Company.company_name,
                func.count(Placement.placement_id).label("hires"),
                func.avg(Placement.package_offered).label("avg_pkg"),
                func.max(Placement.package_offered).label("max_pkg"),
            )
            .join(Placement, Company.company_id == Placement.company_id)
            .filter(Placement.placement_status == "Placed")
            .group_by(Company.company_name)
            .order_by(func.count(Placement.placement_id).desc())
            .all()
        )
        df = pd.DataFrame(rows, columns=["company", "hires", "avg_pkg", "max_pkg"])
        df["avg_pkg"] = df["avg_pkg"].astype(float).round(2)
        df["max_pkg"] = df["max_pkg"].astype(float).round(2)
        return df
    finally:
        session.close()


# ── CRUD helpers ───────────────────────────────────────────────────────────────

def add_student(data: dict) -> bool:
    """Insert a new student + blank skill record."""
    from database.db_connection import get_db
    try:
        with get_db() as db:
            student = Student(**{k: v for k, v in data.items()
                                 if k in Student.__table__.columns.keys()})
            db.add(student)
            db.flush()
            # Create blank skill record
            skill = Skill(student_id=student.student_id)
            db.add(skill)
        return True
    except Exception as e:
        print(f"Error adding student: {e}")
        return False


def update_student(student_id: int, data: dict) -> bool:
    """Update student fields."""
    from database.db_connection import get_db
    try:
        with get_db() as db:
            db.query(Student).filter_by(student_id=student_id).update(data)
        return True
    except Exception as e:
        print(f"Error updating student {student_id}: {e}")
        return False


def delete_student(student_id: int) -> bool:
    """Delete a student (cascades to skills and placements)."""
    from database.db_connection import get_db
    try:
        with get_db() as db:
            student = db.query(Student).filter_by(student_id=student_id).first()
            if student:
                db.delete(student)
        return True
    except Exception as e:
        print(f"Error deleting student {student_id}: {e}")
        return False


def upsert_skills(student_id: int, skill_data: dict) -> bool:
    """Insert or update skill record for a student."""
    from database.db_connection import get_db
    try:
        with get_db() as db:
            existing = db.query(Skill).filter_by(student_id=student_id).first()
            if existing:
                for k, v in skill_data.items():
                    setattr(existing, k, v)
            else:
                skill = Skill(student_id=student_id, **skill_data)
                db.add(skill)
        return True
    except Exception as e:
        print(f"Error upserting skills for {student_id}: {e}")
        return False


def upsert_placement(student_id: int, placement_data: dict) -> bool:
    """Insert or update placement record."""
    from database.db_connection import get_db
    try:
        with get_db() as db:
            existing = db.query(Placement).filter_by(student_id=student_id).first()
            if existing:
                for k, v in placement_data.items():
                    setattr(existing, k, v)
            else:
                p = Placement(student_id=student_id, **placement_data)
                db.add(p)
        return True
    except Exception as e:
        print(f"Error upserting placement for {student_id}: {e}")
        return False


# ── CSV export helpers ─────────────────────────────────────────────────────────

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return DataFrame as UTF-8 encoded CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


# Fix missing import
from sqlalchemy import Integer
