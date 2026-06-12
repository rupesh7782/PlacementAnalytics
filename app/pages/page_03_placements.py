"""
app/pages/03_Placements.py
---------------------------
Track and manage student placement records.
"""

import streamlit as st
import pandas as pd
import datetime
from app.utils.data_utils import (
    fetch_all_students, fetch_placements_dataframe,
    fetch_companies, upsert_placement, df_to_csv_bytes
)
from database.db_connection import get_db_session, Company


def show():
    st.title("🎓 Placement Tracking")
    st.markdown("Record and manage student placement outcomes.")

    tab_list, tab_record = st.tabs(["📋 Placement Records", "📝 Add / Update Record"])

    # ── LIST ──────────────────────────────────────────────────────────────────
    with tab_list:
        df = fetch_placements_dataframe()
        if df.empty:
            st.info("No placement records yet.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                status_f = st.multiselect("Status", ["Placed", "Not Placed", "In Progress"])
            with col_f2:
                branch_f = st.multiselect("Branch", sorted(df["branch"].unique()))
            with col_f3:
                company_f = st.multiselect("Company", sorted(df["company_name"].dropna().unique()))

            fdf = df.copy()
            if status_f:  fdf = fdf[fdf["placement_status"].isin(status_f)]
            if branch_f:  fdf = fdf[fdf["branch"].isin(branch_f)]
            if company_f: fdf = fdf[fdf["company_name"].isin(company_f)]

            # Highlight placed rows
            def row_color(row):
                if row.placement_status == "Placed":
                    return ["background-color: #d1fae5"] * len(row)
                elif row.placement_status == "Not Placed":
                    return ["background-color: #fee2e2"] * len(row)
                return [""] * len(row)

            styled = fdf.rename(columns={
                "student_code": "ID", "name": "Name", "branch": "Branch",
                "cgpa": "CGPA", "company_name": "Company",
                "package_offered": "Package (LPA)", "placement_status": "Status",
                "interview_date": "Interview", "selection_result": "Result"
            })

            st.dataframe(styled, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Download Placement Report",
                data=df_to_csv_bytes(fdf),
                file_name="placement_report.csv", mime="text/csv"
            )

            # Summary stats
            st.divider()
            placed = df[df["placement_status"] == "Placed"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Records", len(df))
            c2.metric("Placed", len(placed))
            c3.metric("Avg Package", f"₹{placed['package_offered'].astype(float).mean():.2f} LPA"
                       if not placed.empty else "—")
            c4.metric("Top Package", f"₹{placed['package_offered'].astype(float).max():.2f} LPA"
                       if not placed.empty else "—")

    # ── ADD / UPDATE ──────────────────────────────────────────────────────────
    with tab_record:
        st.subheader("Record Placement Outcome")

        students_df  = fetch_all_students()
        companies_df = fetch_companies()

        if students_df.empty:
            st.warning("Add students first before recording placements.")
            return

        student_opts = {
            f"{r['student_code']} – {r['name']}": r["student_id"]
            for _, r in students_df.iterrows()
        }
        company_opts = {r["company_name"]: r["company_id"]
                        for _, r in companies_df.iterrows()}

        with st.form("placement_form"):
            chosen_student = st.selectbox("Select Student", list(student_opts.keys()))
            student_id     = student_opts[chosen_student]

            col1, col2 = st.columns(2)
            with col1:
                placement_status = st.selectbox(
                    "Placement Status", ["Not Placed", "Placed", "In Progress"])
                company_choice = st.selectbox(
                    "Company", ["— None —"] + list(company_opts.keys()))
                package = st.number_input("Package Offered (LPA)", 0.0, 100.0, 0.0, 0.5)

            with col2:
                selection_result = st.selectbox(
                    "Selection Result", ["Pending", "Selected", "Rejected", "Waitlisted"])
                interview_date   = st.date_input("Interview Date",
                                                  value=datetime.date.today())
                offer_date       = st.date_input("Offer Letter Date",
                                                  value=None)

            notes = st.text_area("Notes / Remarks")

            if st.form_submit_button("💾 Save Placement", type="primary"):
                company_id = (
                    company_opts.get(company_choice)
                    if company_choice != "— None —" else None
                )
                data = {
                    "company_id":       company_id,
                    "package_offered":  package if package > 0 else None,
                    "placement_status": placement_status,
                    "interview_date":   interview_date,
                    "selection_result": selection_result,
                    "offer_letter_date": offer_date,
                    "notes":            notes or None,
                }
                ok = upsert_placement(student_id, data)
                if ok:
                    st.success(f"✅ Placement record saved for **{chosen_student}**!")
                else:
                    st.error("❌ Failed to save placement record.")

        # ── Add new company ───────────────────────────────────────────────────
        with st.expander("➕ Add New Company"):
            with st.form("add_company_form", clear_on_submit=True):
                cn = st.text_input("Company Name *")
                ci = st.text_input("Industry")
                cl = st.text_input("Location")
                if st.form_submit_button("Add Company"):
                    if cn:
                        from database.db_connection import get_db, Company
                        try:
                            with get_db() as db:
                                db.add(Company(company_name=cn, industry=ci, location=cl))
                            st.success(f"✅ Company **{cn}** added!")
                        except Exception as e:
                            st.error(f"❌ {e}")
                    else:
                        st.error("Company name is required.")
