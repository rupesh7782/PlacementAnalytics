"""
app/pages/04_Prediction.py
---------------------------
Placement Prediction using ML models with skill gap analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from models.ml_model import predict_placement, analyse_skill_gap, train_models, load_training_data_from_db
from app.components.charts import model_comparison_bar, feature_importance_bar, confusion_matrix_heatmap


# ── Cached training ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🤖 Training ML models …")
def get_trained_models():
    try:
        df = load_training_data_from_db()
    except Exception:
        df = None
    return train_models(df)


def probability_gauge(prob: float, category: str) -> go.Figure:
    color_map = {"High Chance": "#10B981", "Medium Chance": "#F59E0B", "Low Chance": "#EF4444"}
    color = color_map.get(category, "#6B7280")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob,
        number={"suffix": "%", "font": {"size": 48, "color": color}},
        title={"text": f"<b>{category}</b>", "font": {"size": 22}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,  40], "color": "#FEE2E2"},
                {"range": [40, 70], "color": "#FEF3C7"},
                {"range": [70, 100], "color": "#D1FAE5"},
            ],
        }
    ))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=60, b=20, l=20, r=20))
    return fig


def show():
    st.title("🤖 Placement Prediction & Skill Gap Analysis")
    st.markdown("Enter a student profile to predict placement probability and identify skill gaps.")

    tab_predict, tab_metrics = st.tabs(["🎯 Predict", "📊 Model Metrics"])

    # ── PREDICTION ────────────────────────────────────────────────────────────
    with tab_predict:
        col_form, col_result = st.columns([1, 1])

        with col_form:
            st.subheader("Student Profile")

            with st.form("prediction_form"):
                cgpa = st.slider("CGPA", 0.0, 10.0, 7.5, 0.1,
                                  help="Cumulative Grade Point Average (0–10)")
                apt  = st.slider("Aptitude Score", 0.0, 100.0, 65.0, 0.5,
                                  help="Score out of 100")
                comm = st.slider("Communication Score", 0.0, 10.0, 7.0, 0.1,
                                  help="Score out of 10")

                st.markdown("**Technical Skills (0–10)**")
                c1, c2 = st.columns(2)
                with c1:
                    py  = st.slider("Python",     0, 10, 6)
                    sql = st.slider("SQL",         0, 10, 5)
                    js  = st.slider("JavaScript",  0, 10, 4)
                with c2:
                    ja   = st.slider("Java",       0, 10, 5)
                    html = st.slider("HTML/CSS",   0, 10, 5)

                predict_btn = st.form_submit_button("🔍 Predict Placement", type="primary",
                                                     use_container_width=True)

        with col_result:
            if predict_btn:
                with st.spinner("Analysing profile …"):
                    result = predict_placement(cgpa, apt, comm, py, ja, sql, html, js)
                    gap    = analyse_skill_gap(cgpa, apt, comm, py, ja, sql, html, js)

                # ── Gauge ──
                st.plotly_chart(
                    probability_gauge(result["probability"], result["category"]),
                    use_container_width=True
                )

                # ── Per-model breakdown ──
                st.markdown(
                    f"""
                    | Model | Probability |
                    |---|---|
                    | Logistic Regression | **{result['lr_probability']}%** |
                    | Random Forest       | **{result['rf_probability']}%** |
                    | **Ensemble Avg**    | **{result['probability']}%** |
                    """
                )

                st.divider()

                # ── Skill gap analysis ──
                st.subheader("🔍 Skill Gap Analysis")
                st.info(f"💡 {gap['summary']}")

                if gap["cgpa_gap"]:
                    st.warning(
                        f"📚 **CGPA Alert** — Current: {gap['cgpa_gap']['current']} | "
                        f"Target: {gap['cgpa_gap']['target']} — "
                        f"{gap['cgpa_gap']['advice']}"
                    )

                if gap["strengths"]:
                    st.success(f"✅ **Strengths:** {', '.join(gap['strengths'])}")

                if gap["gaps"]:
                    st.markdown("**Areas to Improve:**")
                    for g in gap["gaps"]:
                        with st.expander(
                            f"⚠️ {g['skill']} — Current: {g['current']} | "
                            f"Target: {g['target']} ({g['gap_pct']}% gap)"
                        ):
                            st.markdown(f"**Recommended Resources:** {g['course']}")
                else:
                    st.balloons()
                    st.success("🎉 Excellent profile! No major skill gaps detected.")

            else:
                st.info("👈 Fill in the student profile and click **Predict Placement**.")

    # ── MODEL METRICS ─────────────────────────────────────────────────────────
    with tab_metrics:
        st.subheader("📊 Model Evaluation Metrics")

        if st.button("🔄 (Re-)Train Models", type="primary"):
            st.cache_resource.clear()
            st.rerun()

        results = get_trained_models()

        # Comparison bar chart
        st.plotly_chart(model_comparison_bar(results), use_container_width=True)

        col_lr, col_rf = st.columns(2)

        with col_lr:
            st.markdown("### Logistic Regression")
            lr = results["Logistic Regression"]
            st.metric("Accuracy",   f"{lr['accuracy']*100:.2f}%")
            st.metric("F1 Score",   f"{lr['f1']:.4f}")
            st.metric("ROC-AUC",    f"{lr['roc_auc']:.4f}")
            st.metric("CV Accuracy",f"{lr['cv_accuracy']*100:.2f}%")
            st.plotly_chart(
                confusion_matrix_heatmap(lr["confusion_matrix"], "Logistic Regression"),
                use_container_width=True
            )
            with st.expander("Full Classification Report"):
                st.code(lr["classification_report"])

        with col_rf:
            st.markdown("### Random Forest")
            rf = results["Random Forest"]
            st.metric("Accuracy",    f"{rf['accuracy']*100:.2f}%")
            st.metric("F1 Score",    f"{rf['f1']:.4f}")
            st.metric("ROC-AUC",     f"{rf['roc_auc']:.4f}")
            st.metric("CV Accuracy", f"{rf['cv_accuracy']*100:.2f}%")
            st.plotly_chart(
                confusion_matrix_heatmap(rf["confusion_matrix"], "Random Forest"),
                use_container_width=True
            )
            st.plotly_chart(
                feature_importance_bar(rf["feature_importances"]),
                use_container_width=True
            )
            with st.expander("Full Classification Report"):
                st.code(rf["classification_report"])
