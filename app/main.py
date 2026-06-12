"""
app/main.py
------------
Entry point for the Placement Analytics & Prediction System.
Run with:  streamlit run app/main.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title  = "Placement Analytics System",
    page_icon   = "🎓",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ── Initialize Session State for Navigation ────────────────────────────────────
if "active_page" not in st.session_state:
    st.session_state.active_page = "🏠 Home"

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 🔥 FORCE HIDE the default Streamlit sidebar navigation 🔥 */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%);
}
section[data-testid="stSidebar"] * { color: #e0e7ff !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label { color: #c7d2fe !important; }

/* KPI metric cards */
[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.7rem; font-weight: 700; color: #1e293b;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    font-weight: 600;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #4F46E5, #7C3AED);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #4338CA, #6D28D9);
}

/* Data tables */
.dataframe thead th { background: #4F46E5 !important; color: white !important; }

/* Divider colour */
hr { border-color: #e2e8f0; }

/* Main area padding */
.main .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
        <div style='font-size:2.5rem;'>🎓</div>
        <div style='font-size:1.1rem; font-weight:700; letter-spacing:0.5px;'>
            Placement Analytics
        </div>
        <div style='font-size:0.75rem; opacity:0.75; margin-top:2px;'>
            Training & Placement Cell
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # The radio button is now tied to st.session_state.active_page
    page = st.radio(
        "Navigation",
        options=[
            "🏠 Home",
            "📊 Dashboard",
            "👥 Students",
            "🎓 Placements",
            "🤖 Prediction",
            "📄 Reports",
            "⚙️ Settings",
        ],
        key="active_page",
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("""
    <div style='font-size:0.7rem; opacity:0.6; text-align:center;'>
        Built with Streamlit + scikit-learn<br>© 2025 T&P Cell
    </div>
    """, unsafe_allow_html=True)

# ── Page routing ───────────────────────────────────────────────────────────────

if page == "🏠 Home":
    st.title("🎓 Placement Analytics & Prediction System")
    st.markdown("""
    Welcome to the **Training & Placement Cell Management System** — a comprehensive
    platform for tracking student placements, analysing trends, and predicting
    placement outcomes using Machine Learning.
    """)
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 📊 Analytics Dashboard
        Real-time KPIs, branch-wise statistics, company hiring trends, and skill distribution charts.
        """)
        # Updated to correctly change the page via session state
        if st.button("Go to Dashboard →", key="b1"): 
            st.session_state.active_page = "📊 Dashboard"
            st.rerun()

    with col2:
        st.markdown("""
        ### 🤖 ML Prediction
        Predict placement probability using Logistic Regression & Random Forest with skill gap insights.
        """)
        if st.button("Try Prediction →", key="b2"): 
            st.session_state.active_page = "🤖 Prediction"
            st.rerun()

    with col3:
        st.markdown("""
        ### 📄 Reports
        Generate and download student, placement, and branch-wise reports in CSV or Excel format.
        """)
        if st.button("View Reports →", key="b3"): 
            st.session_state.active_page = "📄 Reports"
            st.rerun()

    st.divider()
    st.markdown("#### Quick Feature Overview")
    features = {
        "Student Management": "Add, update, delete students; manage technical & soft skills.",
        "Placement Tracking": "Record company visits, interview dates, packages, and outcomes.",
        "Analytics Dashboard": "Visualise KPIs, trends, and performance across branches.",
        "ML Prediction": "Predict placement chances with confidence % and model comparison.",
        "Skill Gap Analysis": "Identify missing skills and get course recommendations.",
        "Report Generation": "Export all data to Excel or CSV in one click.",
    }
    for feat, desc in features.items():
        st.markdown(f"- **{feat}** — {desc}")

elif page == "📊 Dashboard":
    from app.pages.dashboard import show
    show()

elif page == "👥 Students":
    from app.pages.students import show
    show()

elif page == "🎓 Placements":
    from app.pages.placements import show
    show()

elif page == "🤖 Prediction":
    from app.pages.prediction import show
    show()

elif page == "📄 Reports":
    from app.pages.reports import show
    show()

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.subheader("Database Configuration")
    db_url = st.text_input(
        "DATABASE_URL",
        value=os.getenv("DATABASE_URL", "postgresql://postgres:rc%401710@localhost:5432/placement_db"),
        type="password"
    )
    if st.button("Test Connection"):
        try:
            from sqlalchemy import create_engine, text
            eng = create_engine(db_url)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.success("✅ Connection successful!")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")

    st.divider()
    st.subheader("ML Model Management")
    if st.button("🔄 Retrain Models"):
        import streamlit as st
        st.cache_resource.clear()
        st.success("Cache cleared. Models will retrain on next visit to Prediction page.")

    st.divider()
    st.subheader("Database Initialisation")
    st.warning("⚠️ The button below creates tables if they don't exist. Safe to run multiple times.")
    if st.button("🗄️ Initialise Database Tables"):
        try:
            from database.db_connection import init_db
            init_db()
            st.success("✅ Database tables created/verified.")
        except Exception as e:
            st.error(f"❌ {e}")

    if st.button("🌱 Seed Sample Data (200 students)"):
        try:
            from data.seed_data import seed_students
            from database.db_connection import get_db
            with get_db() as db:
                seed_students(db, n=200)
            st.success("✅ Sample data seeded!")
        except Exception as e:
            st.error(f"❌ {e}")
