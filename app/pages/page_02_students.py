import streamlit as st
import pandas as pd
from app.utils.data_utils import (
    fetch_all_students, add_student, update_student,
    delete_student, upsert_skills, upsert_placement,
    fetch_companies, df_to_csv_bytes
)

# This is the magic line that fixes the NameError:
from database.db_connection import get_db_session, Student, Skill 

BRANCHES = [
    "Computer Science", "Information Technology",
    "Electronics & Communication", "Mechanical Engineering",
    "Civil Engineering", "Electrical Engineering",
    "Data Science", "Artificial Intelligence"
]git --version

def show():
    st.title("👥 Student Management")
    st.markdown("Add, view, edit, and remove student records.")

    tab_list, tab_add, tab_edit, tab_skills = st.tabs(
        ["📋 All Students", "➕ Add Student", "✏️ Edit / Delete", "🧠 Update Skills"]
    )

    # ── LIST ──────────────────────────────────────────────────────────────────
    with tab_list:
        df = fetch_all_students()
        if df.empty:
            st.info("No students found. Add some using the 'Add Student' tab.")
        else:
            st.markdown(f"**{len(df)} students** in the database.")

            # Filters
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                branch_filter = st.multiselect("Filter by Branch",
                                               options=sorted(df["branch"].unique()),
                                               default=[])
            with col_f2:
                year_filter = st.multiselect("Graduation Year",
                                             options=sorted(df["graduation_year"].unique()),
                                             default=[])
            with col_f3:
                status_filter = st.multiselect("Placement Status",
                                               options=["Placed", "Not Placed", "In Progress"],
                                               default=[])

            fdf = df.copy()
            if branch_filter:
                fdf = fdf[fdf["branch"].isin(branch_filter)]
            if year_filter:
                fdf = fdf[fdf["graduation_year"].isin(year_filter)]
            if status_filter:
                fdf = fdf[fdf["placement_status"].isin(status_filter)]

            st.dataframe(
                fdf.rename(columns={
                    "student_code": "ID", "name": "Name", "branch": "Branch",
                    "cgpa": "CGPA", "graduation_year": "Grad Year",
                    "email": "Email", "phone": "Phone",
                    "placement_status": "Status", "package_offered": "Package (LPA)",
                    "company_name": "Company"
                }),
                use_container_width=True, hide_index=True
            )
            st.download_button(
                "⬇️ Download CSV", data=df_to_csv_bytes(fdf),
                file_name="students.csv", mime="text/csv"
            )

    # ── ADD ───────────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add New Student")
        with st.form("add_student_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                code  = st.text_input("Student Code *", placeholder="STU0201")
                name  = st.text_input("Full Name *")
                email = st.text_input("Email *")
                phone = st.text_input("Phone")
            with c2:
                branch   = st.selectbox("Branch *", BRANCHES)
                cgpa     = st.number_input("CGPA (0–10)", 0.0, 10.0, 7.5, 0.01)
                grad_yr  = st.number_input("Graduation Year", 2020, 2030, 2025, 1)

            submitted = st.form_submit_button("➕ Add Student", type="primary")
            if submitted:
                if not all([code, name, email]):
                    st.error("Student Code, Name, and Email are required.")
                else:
                    ok = add_student({
                        "student_code": code, "name": name, "branch": branch,
                        "cgpa": cgpa, "graduation_year": int(grad_yr),
                        "email": email, "phone": phone
                    })
                    if ok:
                        st.success(f"✅ Student **{name}** added successfully!")
                    else:
                        st.error("❌ Failed to add student. Student code or email may already exist.")

    # ── EDIT / DELETE ─────────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Edit or Delete a Student")
        df_all = fetch_all_students()
        if df_all.empty:
            st.info("No students to edit.")
        else:
            options = {f"{r['student_code']} – {r['name']}": r["student_id"]
                       for _, r in df_all.iterrows()}
            chosen = st.selectbox("Select Student", list(options.keys()))
            student_id = options[chosen]
            session = get_db_session()
            student = session.query(Student).filter_by(student_id=student_id).first()
            session.close()

            if student:
                with st.form("edit_student_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_name  = st.text_input("Full Name",  value=student.name)
                        new_email = st.text_input("Email",      value=student.email or "")
                        new_phone = st.text_input("Phone",      value=student.phone or "")
                    with c2:
                        new_branch  = st.selectbox("Branch", BRANCHES,
                                                   index=BRANCHES.index(student.branch)
                                                   if student.branch in BRANCHES else 0)
                        new_cgpa    = st.number_input("CGPA", 0.0, 10.0,
                                                      float(student.cgpa or 0), 0.01)
                        new_grad_yr = st.number_input("Graduation Year", 2020, 2030,
                                                      int(student.graduation_year), 1)

                    col_save, col_del = st.columns([3, 1])
                    with col_save:
                        save = st.form_submit_button("💾 Save Changes", type="primary")
                    with col_del:
                        delete = st.form_submit_button("🗑️ Delete", type="secondary")

                    if save:
                        ok = update_student(student_id, {
                            "name": new_name, "email": new_email,
                            "phone": new_phone, "branch": new_branch,
                            "cgpa": new_cgpa, "graduation_year": int(new_grad_yr)
                        })
                        st.success("✅ Updated!") if ok else st.error("❌ Update failed.")

                    if delete:
                        ok = delete_student(student_id)
                        st.success("🗑️ Deleted!") if ok else st.error("❌ Delete failed.")

    # ── SKILLS ────────────────────────────────────────────────────────────────
    with tab_skills:
        st.subheader("Update Student Skills")
        df_all = fetch_all_students()
        if df_all.empty:
            st.info("No students found.")
        else:
            options = {f"{r['student_code']} – {r['name']}": r["student_id"]
                       for _, r in df_all.iterrows()}
            chosen     = st.selectbox("Select Student", list(options.keys()),
                                       key="skill_student")
            student_id = options[chosen]

            
            session = get_db_session()
            skill   = session.query(Skill).filter_by(student_id=student_id).first()
            session.close()

            with st.form("skills_form"):
                st.markdown("**Technical Skills (0–10)**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    py  = st.slider("Python",     0, 10, int(skill.python_score  if skill else 0))
                    ja  = st.slider("Java",        0, 10, int(skill.java_score    if skill else 0))
                with c2:
                    sql = st.slider("SQL",         0, 10, int(skill.sql_score     if skill else 0))
                    html= st.slider("HTML/CSS",    0, 10, int(skill.html_css_score if skill else 0))
                with c3:
                    js  = st.slider("JavaScript",  0, 10, int(skill.javascript_score if skill else 0))

                st.markdown("**Soft Skills**")
                col_a, col_b = st.columns(2)
                with col_a:
                    apt  = st.number_input("Aptitude Score (0–100)", 0.0, 100.0,
                                           float(skill.aptitude_score if skill else 50), 0.5)
                with col_b:
                    comm = st.number_input("Communication Score (0–10)", 0.0, 10.0,
                                           float(skill.communication_score if skill else 5), 0.1)

                if st.form_submit_button("💾 Save Skills", type="primary"):
                    ok = upsert_skills(student_id, {
                        "python_score": py, "java_score": ja,
                        "sql_score": sql, "html_css_score": html,
                        "javascript_score": js, "aptitude_score": apt,
                        "communication_score": comm
                    })
                    st.success("✅ Skills saved!") if ok else st.error("❌ Save failed.")
