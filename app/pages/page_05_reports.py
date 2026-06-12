"""
app/pages/05_Reports.py
------------------------
Generate and download placement, student, and branch-wise reports.
"""

import streamlit as st
import pandas as pd
import io
from app.utils.data_utils import (
    fetch_all_students, fetch_placements_dataframe,
    get_branch_stats, get_company_hiring_stats, df_to_csv_bytes
)


def _excel_bytes(dfs_sheets: dict) -> bytes:
    """Convert a dict of {sheet_name: DataFrame} to Excel bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet, df in dfs_sheets.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)
    return buf.getvalue()


def show():
    st.title("📄 Reports")
    st.markdown("Generate downloadable reports for students, placements, and branches.")

    tab_student, tab_placement, tab_branch, tab_full = st.tabs([
        "🧑 Student Report", "🏢 Placement Report",
        "🌿 Branch Report", "📦 Full Export"
    ])

    # ── STUDENT REPORT ────────────────────────────────────────────────────────
    with tab_student:
        st.subheader("Student Report")
        df = fetch_all_students()
        if df.empty:
            st.info("No data available.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                yr_filter = st.multiselect("Graduation Year",
                                            sorted(df["graduation_year"].unique()))
            with col2:
                br_filter = st.multiselect("Branch", sorted(df["branch"].unique()))

            rdf = df.copy()
            if yr_filter: rdf = rdf[rdf["graduation_year"].isin(yr_filter)]
            if br_filter:  rdf = rdf[rdf["branch"].isin(br_filter)]

            st.dataframe(rdf, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download CSV",
                                   df_to_csv_bytes(rdf),
                                   "student_report.csv", "text/csv")
            with c2:
                st.download_button("⬇️ Download Excel",
                                   _excel_bytes({"Students": rdf}),
                                   "student_report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── PLACEMENT REPORT ──────────────────────────────────────────────────────
    with tab_placement:
        st.subheader("Placement Report")
        pdf = fetch_placements_dataframe()
        if pdf.empty:
            st.info("No placement data available.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st_filter = st.multiselect("Status",
                                            ["Placed", "Not Placed", "In Progress"])
            with col2:
                co_filter = st.multiselect("Company",
                                            sorted(pdf["company_name"].dropna().unique()))

            rpdf = pdf.copy()
            if st_filter: rpdf = rpdf[rpdf["placement_status"].isin(st_filter)]
            if co_filter:  rpdf = rpdf[rpdf["company_name"].isin(co_filter)]

            # Summary metrics
            placed = rpdf[rpdf["placement_status"] == "Placed"]
            m1, m2, m3 = st.columns(3)
            m1.metric("Filtered Records", len(rpdf))
            m2.metric("Placed",           len(placed))
            m3.metric("Avg Package",
                       f"₹{placed['package_offered'].astype(float).mean():.2f} LPA"
                       if not placed.empty else "—")

            st.dataframe(rpdf, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download CSV",
                                   df_to_csv_bytes(rpdf),
                                   "placement_report.csv", "text/csv")
            with c2:
                st.download_button("⬇️ Download Excel",
                                   _excel_bytes({"Placements": rpdf}),
                                   "placement_report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── BRANCH REPORT ─────────────────────────────────────────────────────────
    with tab_branch:
        st.subheader("Branch-wise Placement Report")
        bdf = get_branch_stats()
        if bdf.empty:
            st.info("No data available.")
        else:
            st.dataframe(
                bdf.rename(columns={
                    "branch": "Branch", "total": "Total Students",
                    "placed": "Placed", "not_placed": "Not Placed",
                    "pct_placed": "Placement %"
                }),
                use_container_width=True, hide_index=True
            )

            company_df = get_company_hiring_stats()
            st.subheader("Company Hiring Summary")
            if not company_df.empty:
                st.dataframe(
                    company_df.rename(columns={
                        "company": "Company", "hires": "Hires",
                        "avg_pkg": "Avg Package (LPA)", "max_pkg": "Max Package (LPA)"
                    }),
                    use_container_width=True, hide_index=True
                )

            combined = {"Branch Stats": bdf, "Company Stats": company_df}
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download CSV (Branch)",
                                   df_to_csv_bytes(bdf),
                                   "branch_report.csv", "text/csv")
            with c2:
                st.download_button("⬇️ Download Excel (All)",
                                   _excel_bytes(combined),
                                   "branch_report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── FULL EXPORT ───────────────────────────────────────────────────────────
    with tab_full:
        st.subheader("Full Data Export")
        st.markdown("Export all data across all modules into a single Excel workbook.")

        if st.button("📦 Generate Full Report", type="primary"):
            with st.spinner("Compiling data …"):
                sheets = {
                    "Students":   fetch_all_students(),
                    "Placements": fetch_placements_dataframe(),
                    "Branch Stats": get_branch_stats(),
                    "Company Stats": get_company_hiring_stats(),
                }
            st.success("✅ Report ready!")
            st.download_button(
                "⬇️ Download Full Excel Report",
                data=_excel_bytes(sheets),
                file_name="placement_analytics_full_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
