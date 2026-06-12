"""
models/ml_model.py
-------------------
Machine Learning module for placement prediction.
Trains Logistic Regression & Random Forest on historical data,
evaluates both, and exposes a unified predict() interface.
"""

import numpy as np
import pandas as pd
import pickle
import os
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)
import warnings
warnings.filterwarnings("ignore")

MODEL_DIR  = os.path.join(os.path.dirname(__file__))
LR_PATH    = os.path.join(MODEL_DIR, "logistic_regression.pkl")
RF_PATH    = os.path.join(MODEL_DIR, "random_forest.pkl")
SCALER_PATH= os.path.join(MODEL_DIR, "scaler.pkl")

FEATURE_COLS = [
    "cgpa", "aptitude_score", "communication_score",
    "python_score", "java_score", "sql_score",
    "html_css_score", "javascript_score"
]


# ── Data loading ───────────────────────────────────────────────────────────────

def load_training_data_from_db() -> pd.DataFrame:
    """Pull joined student + skills + placement data from PostgreSQL."""
    from database.db_connection import get_db_session, Student, Skill, Placement
    from sqlalchemy.orm import joinedload

    session = get_db_session()
    try:
        rows = (
            session.query(Student, Skill, Placement)
            .join(Skill,     Student.student_id == Skill.student_id)
            .join(Placement, Student.student_id == Placement.student_id)
            .all()
        )
        records = []
        for student, skill, placement in rows:
            records.append({
                "cgpa":                float(student.cgpa or 0),
                "aptitude_score":      float(skill.aptitude_score or 0),
                "communication_score": float(skill.communication_score or 0),
                "python_score":        int(skill.python_score or 0),
                "java_score":          int(skill.java_score or 0),
                "sql_score":           int(skill.sql_score or 0),
                "html_css_score":      int(skill.html_css_score or 0),
                "javascript_score":    int(skill.javascript_score or 0),
                "placed":              1 if placement.placement_status == "Placed" else 0,
            })
        return pd.DataFrame(records)
    finally:
        session.close()


def generate_synthetic_data(n: int = 300) -> pd.DataFrame:
    """
    Create synthetic training data when DB is empty.
    Mirrors the heuristic logic from seed_data.py.
    """
    np.random.seed(42)
    cgpas  = np.random.uniform(5.0, 9.8, n)
    rows   = []
    for cgpa in cgpas:
        b = int(cgpa)
        apt  = round(float(np.clip(np.random.normal(cgpa * 8, 8), 0, 100)), 2)
        comm = round(float(np.clip(np.random.normal(6 + (cgpa - 5) * 0.5, 1.2), 0, 10)), 2)
        py   = int(np.clip(np.random.randint(b - 2, b + 1), 0, 10))
        ja   = int(np.clip(np.random.randint(b - 3, b + 1), 0, 10))
        sql  = int(np.clip(np.random.randint(b - 3, b + 1), 0, 10))
        html = int(np.clip(np.random.randint(b - 2, b + 1), 0, 10))
        js   = int(np.clip(np.random.randint(b - 3, b + 1), 0, 10))
        score = cgpa * 10 + apt * 0.3 + comm * 5 + (py + ja) * 2
        placed = 1 if score >= np.random.uniform(100, 140) else 0
        rows.append({
            "cgpa": round(cgpa, 2), "aptitude_score": apt,
            "communication_score": comm, "python_score": py,
            "java_score": ja, "sql_score": sql,
            "html_css_score": html, "javascript_score": js,
            "placed": placed
        })
    return pd.DataFrame(rows)


# ── Training ───────────────────────────────────────────────────────────────────

def train_models(df: pd.DataFrame = None):
    """
    Train LR and RF classifiers, save artefacts, return evaluation metrics dict.
    Falls back to synthetic data if df is None or too small.
    """
    if df is None or len(df) < 20:
        print("ℹ️  Using synthetic data for training (insufficient DB records).")
        df = generate_synthetic_data(300)

    X = df[FEATURE_COLS].fillna(0)
    y = df["placed"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features (needed for LR)
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    results = {}

    # ── Logistic Regression ──
    lr = LogisticRegression(max_iter=500, random_state=42)
    lr.fit(X_train_sc, y_train)
    y_pred_lr = lr.predict(X_test_sc)
    y_prob_lr = lr.predict_proba(X_test_sc)[:, 1]
    cv_lr     = cross_val_score(lr, scaler.transform(X), y, cv=5, scoring="accuracy").mean()

    results["Logistic Regression"] = {
        "accuracy":  round(accuracy_score(y_test, y_pred_lr), 4),
        "precision": round(precision_score(y_test, y_pred_lr, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred_lr, zero_division=0), 4),
        "f1":        round(f1_score(y_test, y_pred_lr, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_prob_lr), 4),
        "cv_accuracy": round(cv_lr, 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_lr).tolist(),
        "classification_report": classification_report(y_test, y_pred_lr),
    }

    # ── Random Forest ──
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    cv_rf     = cross_val_score(rf, X, y, cv=5, scoring="accuracy").mean()

    results["Random Forest"] = {
        "accuracy":  round(accuracy_score(y_test, y_pred_rf), 4),
        "precision": round(precision_score(y_test, y_pred_rf, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred_rf, zero_division=0), 4),
        "f1":        round(f1_score(y_test, y_pred_rf, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_prob_rf), 4),
        "cv_accuracy": round(cv_rf, 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_rf).tolist(),
        "classification_report": classification_report(y_test, y_pred_rf),
        "feature_importances": dict(zip(FEATURE_COLS, rf.feature_importances_.round(4).tolist())),
    }

    # ── Persist artefacts ──
    with open(LR_PATH,     "wb") as f: pickle.dump(lr,     f)
    with open(RF_PATH,     "wb") as f: pickle.dump(rf,     f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(scaler, f)

    print("✅ Models trained and saved.")
    return results


# ── Loading saved models ───────────────────────────────────────────────────────

def _load_artefacts():
    """Return (lr, rf, scaler) from disk; train fresh if missing."""
    if not all(os.path.exists(p) for p in [LR_PATH, RF_PATH, SCALER_PATH]):
        train_models()
    with open(LR_PATH,     "rb") as f: lr     = pickle.load(f)
    with open(RF_PATH,     "rb") as f: rf     = pickle.load(f)
    with open(SCALER_PATH, "rb") as f: scaler = pickle.load(f)
    return lr, rf, scaler


# ── Prediction ─────────────────────────────────────────────────────────────────

def predict_placement(
    cgpa: float,
    aptitude_score: float,
    communication_score: float,
    python_score: int = 0,
    java_score: int = 0,
    sql_score: int = 0,
    html_css_score: int = 0,
    javascript_score: int = 0,
) -> dict:
    """
    Predict placement probability for a single student profile.
    Returns a dict with probability, category, and per-model breakdown.
    """
    lr, rf, scaler = _load_artefacts()

    features = np.array([[
        cgpa, aptitude_score, communication_score,
        python_score, java_score, sql_score,
        html_css_score, javascript_score
    ]])

    features_sc = scaler.transform(features)

    lr_prob = float(lr.predict_proba(features_sc)[0, 1])
    rf_prob = float(rf.predict_proba(features)[0, 1])
    avg_prob = (lr_prob + rf_prob) / 2.0

    # Category thresholds
    if avg_prob >= 0.70:
        category = "High Chance"
        colour   = "green"
    elif avg_prob >= 0.40:
        category = "Medium Chance"
        colour   = "orange"
    else:
        category = "Low Chance"
        colour   = "red"

    return {
        "probability":          round(avg_prob * 100, 2),
        "category":             category,
        "colour":               colour,
        "lr_probability":       round(lr_prob * 100, 2),
        "rf_probability":       round(rf_prob * 100, 2),
    }


# ── Skill gap analysis ─────────────────────────────────────────────────────────

SKILL_THRESHOLDS = {
    "python_score":        6,
    "java_score":          5,
    "sql_score":           6,
    "html_css_score":      5,
    "javascript_score":    5,
    "aptitude_score":      60,   # out of 100
    "communication_score": 7,    # out of 10
}

SKILL_COURSES = {
    "python_score":        ("Python", "Python for Everybody – Coursera | Automate the Boring Stuff (free)"),
    "java_score":          ("Java", "Java Programming – Udemy | Oracle Java Tutorials (free)"),
    "sql_score":           ("SQL", "SQL for Data Science – Coursera | SQLZoo (free)"),
    "html_css_score":      ("HTML/CSS", "The Web Developer Bootcamp – Udemy | freeCodeCamp (free)"),
    "javascript_score":    ("JavaScript", "JavaScript Algorithms – freeCodeCamp | The Odin Project (free)"),
    "aptitude_score":      ("Aptitude", "IndiaBIX Practice | RS Aggarwal Aptitude Book | TCS iON PrepZone"),
    "communication_score": ("Communication", "Toastmasters | Coursera Soft Skills | Speak English Professionally – Coursera"),
}

CGPA_THRESHOLD = 7.0


def analyse_skill_gap(
    cgpa: float,
    aptitude_score: float,
    communication_score: float,
    python_score: int = 0,
    java_score: int = 0,
    sql_score: int = 0,
    html_css_score: int = 0,
    javascript_score: int = 0,
) -> dict:
    """
    Compare student scores against thresholds.
    Returns list of gaps with recommendations.
    """
    profile = {
        "python_score":        python_score,
        "java_score":          java_score,
        "sql_score":           sql_score,
        "html_css_score":      html_css_score,
        "javascript_score":    javascript_score,
        "aptitude_score":      aptitude_score,
        "communication_score": communication_score,
    }

    gaps, strengths = [], []

    for key, threshold in SKILL_THRESHOLDS.items():
        value = profile.get(key, 0)
        skill_name, course = SKILL_COURSES[key]
        if value < threshold:
            gap_pct = round((threshold - value) / threshold * 100)
            gaps.append({
                "skill":      skill_name,
                "current":    value,
                "target":     threshold,
                "gap_pct":    gap_pct,
                "course":     course,
            })
        else:
            strengths.append(skill_name)

    cgpa_gap = None
    if cgpa < CGPA_THRESHOLD:
        cgpa_gap = {
            "current": cgpa,
            "target":  CGPA_THRESHOLD,
            "advice":  "Focus on academic performance; aim for CGPA ≥ 7.0 for most MNC shortlisting criteria.",
        }

    # Build a human-readable summary
    if gaps:
        gap_names = [g["skill"] for g in gaps]
        summary = f"Improve {', '.join(gap_names)} to increase placement probability."
    else:
        summary = "Great profile! Focus on maintaining scores and building projects."

    return {
        "gaps":      gaps,
        "strengths": strengths,
        "cgpa_gap":  cgpa_gap,
        "summary":   summary,
    }
