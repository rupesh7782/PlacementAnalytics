# 🎓 Placement Analytics & Prediction System

A full-stack web application for college Training & Placement Cells to **track student data**, **analyse placement trends**, **identify skill gaps**, and **predict placement chances** using Machine Learning.

---

## 📋 Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Database Schema](#database-schema)
5. [Setup Instructions](#setup-instructions)
6. [Running the App](#running-the-app)
7. [ML Models](#ml-models)
8. [Screenshots](#screenshots)
9. [Contributing](#contributing)

---

## ✨ Features

| Module | Description |
|---|---|
| **Student Management** | Add, update, delete students; manage CGPA, branch, contact info |
| **Skills Management** | Track Python, Java, SQL, HTML/CSS, JS, Aptitude, Communication |
| **Placement Tracking** | Record company visits, packages, interview dates, outcomes |
| **Analytics Dashboard** | KPIs, gauges, branch charts, company stats, skill radars |
| **ML Prediction** | Placement probability via Logistic Regression + Random Forest |
| **Skill Gap Analysis** | Identify weak areas, get personalised course recommendations |
| **Reports** | Download student/placement/branch reports as CSV or Excel |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python 3.10+ |
| Database | PostgreSQL 14+ |
| ORM | SQLAlchemy 2.x |
| ML | scikit-learn (LR + Random Forest) |
| Visualisation | Plotly, Matplotlib |
| Excel Export | openpyxl |
| Fake Data | Faker |

---

## 📁 Project Structure

```
placement_analytics/
│
├── app/
│   ├── main.py                    # Streamlit entry point + sidebar nav
│   ├── components/
│   │   └── charts.py              # Reusable Plotly chart functions
│   ├── pages/
│   │   ├── page_01_dashboard.py   # Analytics dashboard
│   │   ├── page_02_students.py    # Student CRUD
│   │   ├── page_03_placements.py  # Placement tracking
│   │   ├── page_04_prediction.py  # ML prediction + skill gap
│   │   └── page_05_reports.py     # Report generation
│   └── utils/
│       └── data_utils.py          # DB query helpers, CRUD, CSV export
│
├── database/
│   ├── db_connection.py           # SQLAlchemy engine, models, session
│   └── schema.sql                 # Raw SQL DDL for manual setup
│
├── data/
│   └── seed_data.py               # Sample data generator (200 students)
│
├── models/
│   ├── ml_model.py                # Training, prediction, skill gap logic
│   ├── logistic_regression.pkl    # (auto-generated on first run)
│   ├── random_forest.pkl          # (auto-generated on first run)
│   └── scaler.pkl                 # (auto-generated on first run)
│
├── .env.example                   # Environment variable template
├── requirements.txt
└── README.md
```

---

## 🗄️ Database Schema

```
students         skills              companies        placements
──────────       ──────────          ──────────       ──────────
student_id  ──── student_id          company_id  ──── company_id
student_code     python_score        company_name     student_id ──┐
name             java_score          industry         package_lpa  │
branch           sql_score           location         status       │
cgpa             html_css_score      website          interview_dt │
graduation_year  javascript_score                     selection    │
email            aptitude_score                       offer_date   │
phone            communication_score                  notes        │
                                                                   │
                                     students.student_id ──────────┘
```

**Relationships:**
- One student → one skills record (1:1)
- One student → many placement records (1:N)
- One company → many placement records (1:N)

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip

### Step 1 — Clone / Download

```bash
git clone https://github.com/yourname/placement_analytics.git
cd placement_analytics
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure PostgreSQL

Create the database:

```sql
-- In psql
CREATE DATABASE placement_db;
```

Copy and edit the env file:

```bash
cp .env.example .env
# Edit .env and set your DATABASE_URL
```

### Step 5 — Initialise the Schema

**Option A — Using the SQL script:**

```bash
psql -U postgres -d placement_db -f database/schema.sql
```

**Option B — Via the app (Settings page):**

Start the app and navigate to **⚙️ Settings → Initialise Database Tables**.

### Step 6 — Seed Sample Data

```bash
python data/seed_data.py
```

This inserts **200 realistic student records** with skills and placements.

Alternatively, use **⚙️ Settings → Seed Sample Data** in the running app.

---

## 🚀 Running the App

```bash
streamlit run app/main.py
```

Open your browser at **http://localhost:8501**

---

## 🤖 ML Models

### Features Used
| Feature | Description |
|---|---|
| CGPA | Academic performance (0–10) |
| Aptitude Score | Logical reasoning (0–100) |
| Communication Score | Soft skills (0–10) |
| Python / Java / SQL / HTML-CSS / JS | Technical skills (0–10 each) |

### Models Trained
- **Logistic Regression** — fast, interpretable baseline
- **Random Forest** — higher accuracy, feature importances

### Evaluation Metrics Displayed
- Accuracy, Precision, Recall, F1, ROC-AUC
- 5-fold Cross-validation Accuracy
- Confusion Matrix Heatmap
- Feature Importance Chart (RF)
- Classification Report

### Prediction Output
| Probability | Category |
|---|---|
| ≥ 70% | 🟢 High Chance |
| 40–69% | 🟡 Medium Chance |
| < 40% | 🔴 Low Chance |

---

## 📊 Skill Gap Analysis

The system compares a student's skill scores against industry thresholds:

| Skill | Target Score |
|---|---|
| Python | ≥ 6/10 |
| Java | ≥ 5/10 |
| SQL | ≥ 6/10 |
| HTML/CSS | ≥ 5/10 |
| JavaScript | ≥ 5/10 |
| Aptitude | ≥ 60/100 |
| Communication | ≥ 7/10 |
| CGPA | ≥ 7.0 |

For each gap, the system recommends specific online courses and resources.

---

## 📄 Reports Available

1. **Student Report** — All student data with filters (branch, year)
2. **Placement Report** — All placement records with filters (status, company)
3. **Branch Report** — Placement % per branch + company hiring stats
4. **Full Export** — Everything in a single multi-sheet Excel workbook

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

---

## 📝 License

MIT License — free for academic and commercial use.
