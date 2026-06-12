"""
app/pages/01_Dashboard.py
--------------------------
Main analytics dashboard showing KPIs, charts, and placement insights.
"""

import streamlit as st
import pandas as pd
from app.utils.data_utils import (
    get_dashboard_kpis, get_branch_stats,
    get_company_hiring_stats, fetch_skills_dataframe,
    fetch_placements_dataframe
)
from app.components.charts import (
    placement_gauge, branch_placement_bar, branch_pie,
    skill_radar, company_hiring_bar, package_distribution,
    cgpa_vs_package, skill_histogram
)


def show():
    st.title("📊 Placement Analytics Dashboard")
    st.markdown("Real-time insights into student placement performance.")
    st.divider()

    # ── KPI cards ──────────────────────────────────────────────────────────────
    kpis = get_dashboard_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("👥 Total Students",   kpis["total_students"])
    with col2:
        st.metric("✅ Placed Students",  kpis["placed_students"])
    with col3:
        st.metric("📈 Placement Rate",   f"{kpis['placement_pct']}%")
    with col4:
        st.metric("💰 Avg Package",      f"₹{kpis['avg_package']} LPA")
    with col5:
        st.metric("🏆 Highest Package",  f"₹{kpis['highest_package']} LPA")

    st.divider()

    # ── Gauge + Branch charts ─────────────────────────────────────────────────
    col_g, col_b = st.columns([1, 2])
    branch_df = get_branch_stats()

    with col_g:
        st.plotly_chart(placement_gauge(kpis["placement_pct"]),
                        use_container_width=True)

    with col_b:
        if not branch_df.empty:
            st.plotly_chart(branch_placement_bar(branch_df),
                            use_container_width=True)

    # ── Branch pie + Skill radar ───────────────────────────────────────────────
    col_p, col_r = st.columns(2)
    skills_df = fetch_skills_dataframe()

    with col_p:
        if not branch_df.empty:
            st.plotly_chart(branch_pie(branch_df), use_container_width=True)

    with col_r:
        if not skills_df.empty:
            skill_cols = ["python_score", "java_score", "sql_score",
                          "html_css_score", "javascript_score"]
            avg_scores = {
                col.replace("_score", "").replace("html_css", "HTML/CSS").title():
                round(float(skills_df[col].mean()), 2)
                for col in skill_cols
            }
            st.plotly_chart(skill_radar(avg_scores), use_container_width=True)

    st.divider()

    # ── Company stats ──────────────────────────────────────────────────────────
    st.subheader("🏢 Company-wise Hiring Statistics")
    company_df = get_company_hiring_stats()
    if not company_df.empty:
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.plotly_chart(company_hiring_bar(company_df), use_container_width=True)
        with col_c2:
            st.dataframe(
                company_df.rename(columns={
                    "company": "Company", "hires": "Hires",
                    "avg_pkg": "Avg Pkg (LPA)", "max_pkg": "Max Pkg (LPA)"
                }),
                use_container_width=True, hide_index=True
            )

    st.divider()

    # ── CGPA vs Package & Package distribution ────────────────────────────────
    st.subheader("📦 Package Insights")
    placements_df = fetch_placements_dataframe()

    if not placements_df.empty and not skills_df.empty:
        merged = placements_df.merge(
            skills_df[["student_id", "cgpa", "name", "branch", "placement_status"]],
            on=["name", "branch", "placement_status"], how="left"
        )
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if "cgpa" in merged.columns:
                st.plotly_chart(cgpa_vs_package(merged), use_container_width=True)
        with col_s2:
            st.plotly_chart(package_distribution(placements_df.merge(
                skills_df[["name", "branch", "placement_status"]],
                on=["name", "branch", "placement_status"], how="left"
            )), use_container_width=True)

    st.divider()

    # ── Skill distributions ────────────────────────────────────────────────────
    st.subheader("🧠 Skill Score Distributions")
    if not skills_df.empty:
        tab1, tab2, tab3 = st.tabs(["Aptitude", "Communication", "Python"])
        with tab1:
            st.plotly_chart(skill_histogram(skills_df, "aptitude_score", "Aptitude Score"),
                            use_container_width=True)
        with tab2:
            st.plotly_chart(skill_histogram(skills_df, "communication_score", "Communication Score"),
                            use_container_width=True)
        with tab3:
            st.plotly_chart(skill_histogram(skills_df, "python_score", "Python Score"),
                            use_container_width=True)
