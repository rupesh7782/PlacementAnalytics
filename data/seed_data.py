"""
data/seed_data.py
------------------
Generates and seeds realistic sample data into the database.
Run once after schema setup:  python data/seed_data.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import datetime
from faker import Faker
from database.db_connection import init_db, get_db, Student, Skill, Company, Placement

fake = Faker("en_IN")
random.seed(42)

# ── Constants ──────────────────────────────────────────────────────────────────
BRANCHES = [
    "Computer Science", "Information Technology", "Electronics & Communication",
    "Mechanical Engineering", "Civil Engineering", "Electrical Engineering",
    "Data Science", "Artificial Intelligence"
]

COMPANIES = [
    ("TCS", "IT Services", "Mumbai"),
    ("Infosys", "IT Services", "Bengaluru"),
    ("Wipro", "IT Services", "Bengaluru"),
    ("Accenture", "Consulting", "Mumbai"),
    ("Cognizant", "IT Services", "Chennai"),
    ("HCL Technologies", "IT Services", "Noida"),
    ("Tech Mahindra", "IT Services", "Pune"),
    ("Capgemini", "IT Consulting", "Mumbai"),
    ("IBM", "Technology", "Bengaluru"),
    ("Amazon", "E-Commerce / Cloud", "Hyderabad"),
    ("Microsoft", "Software", "Hyderabad"),
    ("Google", "Internet / Cloud", "Bengaluru"),
    ("Persistent Systems", "Software", "Pune"),
    ("Mphasis", "IT Services", "Bengaluru"),
    ("L&T Infotech", "IT Services", "Mumbai"),
]

PACKAGE_RANGE = {          # (min_lpa, max_lpa) per company tier
    "Google": (20, 45),
    "Microsoft": (18, 40),
    "Amazon": (15, 35),
    "IBM": (10, 20),
    "Infosys": (3.5, 8),
    "TCS": (3.5, 7),
    "Wipro": (3.5, 7),
    "Accenture": (4.5, 10),
    "Cognizant": (4, 8),
    "HCL Technologies": (3.5, 7),
    "Tech Mahindra": (3.5, 6.5),
    "Capgemini": (4, 8),
    "Persistent Systems": (5, 12),
    "Mphasis": (4, 9),
    "L&T Infotech": (4, 9),
}


def generate_skill_scores(cgpa: float, branch: str) -> dict:
    """Generate correlated skill scores based on CGPA and branch."""
    base = int(cgpa)                            # higher CGPA → better base skills
    cs_branches = {"Computer Science", "Information Technology", "Data Science", "Artificial Intelligence"}

    def rand_skill(low, high):
        return max(0, min(10, random.randint(low, high) + random.randint(-1, 1)))

    if branch in cs_branches:
        return {
            "python_score":        rand_skill(base - 2, base),
            "java_score":          rand_skill(base - 3, base),
            "sql_score":           rand_skill(base - 3, base),
            "html_css_score":      rand_skill(base - 2, base),
            "javascript_score":    rand_skill(base - 3, base),
            "aptitude_score":      round(random.uniform(cgpa * 7, cgpa * 10), 2),
            "communication_score": round(random.uniform(4.0, 9.5), 2),
        }
    else:
        return {
            "python_score":        rand_skill(max(0, base - 5), base - 2),
            "java_score":          rand_skill(0, base - 3),
            "sql_score":           rand_skill(0, base - 3),
            "html_css_score":      rand_skill(0, base - 4),
            "javascript_score":    rand_skill(0, base - 4),
            "aptitude_score":      round(random.uniform(cgpa * 5, cgpa * 9), 2),
            "communication_score": round(random.uniform(3.0, 8.5), 2),
        }


def should_be_placed(cgpa, skills) -> bool:
    """Simple placement heuristic matching real-world patterns."""
    score = (
        cgpa * 10
        + skills["aptitude_score"] * 0.3
        + skills["communication_score"] * 5
        + (skills["python_score"] + skills["java_score"]) * 2
    )
    threshold = random.uniform(100, 140)
    return score >= threshold


def seed_companies(db):
    existing = {c.company_name for c in db.query(Company).all()}
    added = []
    for name, industry, location in COMPANIES:
        if name not in existing:
            c = Company(company_name=name, industry=industry, location=location)
            db.add(c)
            added.append(c)
    db.flush()
    return {c.company_name: c for c in db.query(Company).all()}


def seed_students(db, n=200):
    company_map = seed_companies(db)
    used_codes, used_emails = set(), set()

    for i in range(1, n + 1):
        # ── student code ──
        code = f"STU{i:04d}"
        while code in used_codes:
            code = f"STU{random.randint(1, 9999):04d}"
        used_codes.add(code)

        # ── email ──
        name = fake.name()
        email_base = name.lower().replace(" ", ".") + str(random.randint(1, 999))
        email = f"{email_base}@example.com"
        while email in used_emails:
            email = f"{email_base}{random.randint(1,99)}@example.com"
        used_emails.add(email)

        branch = random.choice(BRANCHES)
        cgpa   = round(random.uniform(5.0, 9.8), 2)
        grad_year = random.choice([2023, 2024, 2025])

        student = Student(
            student_code    = code,
            name            = name,
            branch          = branch,
            cgpa            = cgpa,
            graduation_year = grad_year,
            email           = email,
            phone           = fake.phone_number()[:15],
        )
        db.add(student)
        db.flush()

        # ── skills ──
        skill_data = generate_skill_scores(cgpa, branch)
        skill = Skill(student_id=student.student_id, **skill_data)
        db.add(skill)

        # ── placement ──
        placed = should_be_placed(cgpa, skill_data)
        if placed:
            company_name = random.choice(list(company_map.keys()))
            company      = company_map[company_name]
            lo, hi       = PACKAGE_RANGE.get(company_name, (3.5, 7))
            package      = round(random.uniform(lo, hi), 2)
            idate        = datetime.date(grad_year - 1, random.randint(8, 12), random.randint(1, 28))
            placement = Placement(
                student_id       = student.student_id,
                company_id       = company.company_id,
                package_offered  = package,
                placement_status = "Placed",
                interview_date   = idate,
                selection_result = "Selected",
                offer_letter_date= idate + datetime.timedelta(days=random.randint(7, 30)),
            )
        else:
            placement = Placement(
                student_id       = student.student_id,
                placement_status = "Not Placed",
                selection_result = "Rejected" if random.random() > 0.3 else "Pending",
            )
        db.add(placement)

    db.commit()
    print(f"✅ Seeded {n} students with skills and placements.")


if __name__ == "__main__":
    print("🔧 Initialising database …")
    init_db()
    with get_db() as db:
        print("🌱 Seeding sample data …")
        seed_students(db, n=200)
    print("🎉 Done! Database is ready.")
