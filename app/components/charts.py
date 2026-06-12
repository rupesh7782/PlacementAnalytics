"""
app/components/charts.py
-------------------------
Reusable Plotly chart functions for the analytics dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── Colour palette ─────────────────────────────────────────────────────────────
PRIMARY   = "#4F46E5"   # indigo
SUCCESS   = "#10B981"   # emerald
WARNING   = "#F59E0B"   # amber
DANGER    = "#EF4444"   # red
SECONDARY = "#6B7280"   # grey
PURPLE    = "#7C3AED"

BRANCH_PALETTE = px.colors.qualitative.Set2


# ── KPI gauge ─────────────────────────────────────────────────────────────────

def placement_gauge(pct: float) -> go.Figure:
    """Speedometer gauge for overall placement percentage."""
    fig = go.Figure(go.Indicator(
        mode    = "gauge+number+delta",
        value   = pct,
        number  = {"suffix": "%", "font": {"size": 40}},
        delta   = {"reference": 70, "valueformat": ".1f"},
        title   = {"text": "Placement Rate", "font": {"size": 18}},
        gauge   = {
            "axis":  {"range": [0, 100], "tickwidth": 1},
            "bar":   {"color": PRIMARY},
            "steps": [
                {"range": [0,  40], "color": "#FEE2E2"},
                {"range": [40, 70], "color": "#FEF3C7"},
                {"range": [70, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": DANGER, "width": 4},
                "thickness": 0.75,
                "value": 70
            }
        }
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


# ── Branch-wise bar chart ──────────────────────────────────────────────────────

def branch_placement_bar(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart: placed vs not placed per branch."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Placed",
        x=df["branch"], y=df["placed"],
        marker_color=SUCCESS, text=df["placed"], textposition="auto"
    ))
    fig.add_trace(go.Bar(
        name="Not Placed",
        x=df["branch"], y=df["not_placed"],
        marker_color=DANGER, text=df["not_placed"], textposition="auto"
    ))
    fig.update_layout(
        barmode="group", title="Branch-wise Placement Statistics",
        xaxis_title="Branch", yaxis_title="Number of Students",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=400, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-30)
    )
    return fig


def branch_pie(df: pd.DataFrame) -> go.Figure:
    """Pie chart of branch-wise placement percentage."""
    fig = px.pie(
        df, names="branch", values="pct_placed",
        title="Placement % by Branch",
        color_discrete_sequence=BRANCH_PALETTE,
        hole=0.4
    )
    fig.update_traces(textinfo="label+percent")
    fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)",
                      showlegend=False)
    return fig


# ── Skill distribution ─────────────────────────────────────────────────────────

def skill_radar(avg_scores: dict) -> go.Figure:
    """Radar chart of average skill scores."""
    labels  = list(avg_scores.keys())
    values  = list(avg_scores.values())
    values += [values[0]]          # close the polygon
    labels += [labels[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values, theta=labels,
        fill="toself", fillcolor=f"rgba(79,70,229,0.25)",
        line=dict(color=PRIMARY, width=2)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        title="Average Skill Profile (Technical)",
        height=380, paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def skill_histogram(df: pd.DataFrame, skill_col: str, label: str) -> go.Figure:
    """Distribution histogram for a given skill column."""
    fig = px.histogram(
        df, x=skill_col, nbins=20, color="placement_status",
        color_discrete_map={"Placed": SUCCESS, "Not Placed": DANGER},
        title=f"{label} Distribution",
        labels={skill_col: label, "count": "Students"},
        barmode="overlay"
    )
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)")
    return fig


# ── Company-wise stats ─────────────────────────────────────────────────────────

def company_hiring_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top hiring companies."""
    fig = px.bar(
        df.head(15), x="hires", y="company",
        orientation="h", text="hires",
        color="avg_pkg", color_continuous_scale="Blues",
        title="Top Hiring Companies",
        labels={"hires": "Students Hired", "company": "", "avg_pkg": "Avg Package (LPA)"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=450, yaxis=dict(autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def package_distribution(df: pd.DataFrame) -> go.Figure:
    """Box plot of package distribution by branch."""
    placed = df[df["placement_status"] == "Placed"].copy()
    placed["package_offered"] = placed["package_offered"].astype(float)
    fig = px.box(
        placed, x="branch", y="package_offered",
        color="branch", title="Package Distribution by Branch (LPA)",
        points="all", color_discrete_sequence=BRANCH_PALETTE
    )
    fig.update_layout(
        height=420, xaxis=dict(tickangle=-30),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# ── ML model metrics ───────────────────────────────────────────────────────────

def model_comparison_bar(results: dict) -> go.Figure:
    """Grouped bar comparing LR vs RF across metrics."""
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    labels  = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC"]
    fig = go.Figure()
    colors = [PRIMARY, SUCCESS]
    for (model_name, scores), color in zip(results.items(), colors):
        fig.add_trace(go.Bar(
            name=model_name,
            x=labels,
            y=[scores[m] for m in metrics],
            marker_color=color,
            text=[f"{scores[m]:.3f}" for m in metrics],
            textposition="outside"
        ))
    fig.update_layout(
        barmode="group", title="Model Performance Comparison",
        yaxis=dict(range=[0, 1.1]),
        height=380, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def feature_importance_bar(importances: dict) -> go.Figure:
    """Horizontal bar chart for RF feature importances."""
    df = pd.DataFrame(list(importances.items()), columns=["Feature", "Importance"])
    df = df.sort_values("Importance", ascending=True)
    nice = {
        "cgpa": "CGPA", "aptitude_score": "Aptitude",
        "communication_score": "Communication",
        "python_score": "Python", "java_score": "Java",
        "sql_score": "SQL", "html_css_score": "HTML/CSS",
        "javascript_score": "JavaScript"
    }
    df["Feature"] = df["Feature"].map(nice)
    fig = px.bar(
        df, x="Importance", y="Feature", orientation="h",
        title="Feature Importances (Random Forest)",
        color="Importance", color_continuous_scale="Purples"
    )
    fig.update_layout(
        height=360, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", showlegend=False
    )
    return fig


def confusion_matrix_heatmap(cm: list, model_name: str) -> go.Figure:
    """Heatmap of confusion matrix."""
    z     = cm
    x_lbl = ["Predicted Not Placed", "Predicted Placed"]
    y_lbl = ["Actual Not Placed",     "Actual Placed"]
    fig = go.Figure(go.Heatmap(
        z=z, x=x_lbl, y=y_lbl,
        colorscale="Blues",
        text=z, texttemplate="%{text}",
        showscale=False
    ))
    fig.update_layout(
        title=f"Confusion Matrix – {model_name}",
        height=300, paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# ── CGPA vs package scatter ────────────────────────────────────────────────────

def cgpa_vs_package(df: pd.DataFrame) -> go.Figure:
    placed = df[df["placement_status"] == "Placed"].copy()
    placed["package_offered"] = placed["package_offered"].astype(float)
    placed["cgpa"]            = placed["cgpa"].astype(float)
    fig = px.scatter(
        placed, x="cgpa", y="package_offered",
        color="branch", size="package_offered",
        hover_name="name",
        title="CGPA vs Package Offered",
        labels={"cgpa": "CGPA", "package_offered": "Package (LPA)"},
        color_discrete_sequence=BRANCH_PALETTE,
        trendline="ols"
    )
    fig.update_layout(
        height=420, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig
