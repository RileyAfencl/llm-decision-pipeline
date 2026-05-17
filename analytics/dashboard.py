from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


CSV_PATH = Path("experiments/temp_stability/results.csv")

PROFILE_LABELS = {
    "v1_low_temp": "Low Temp",
    "v2_mid_temp": "Mid Temp",
    "v3_high_temp": "High Temp",
}

EXPERIMENT_LABELS = {
    "temp_stability_fixed_eval_v1": "Fixed Eval",
    "temp_stability_variable_eval_v1": "Variable Eval",
}

PROFILE_ORDER = ["Low Temp", "Mid Temp", "High Temp"]

COLOR_MAP = {
    "Fixed Eval": "#7DD3FC",     # Light cyan
    "Variable Eval": "#2563EB",  # Royal blue
}

def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["profile_label"] = df["temperature_profile"].map(PROFILE_LABELS)
    df["experiment_label"] = df["experiment_id"].map(EXPERIMENT_LABELS)
    return df

def apply_outline_style(fig) -> None:
    for trace in fig.data:
        trace.marker.color = COLOR_MAP[trace.name]  
        trace.marker.line.width = 3   
        trace.marker.line.color = "white" 

def apply_chart_theme(fig) -> None:
    fig.update_layout(
        title_x=.2,
        title_font=dict(size=24),
        font=dict(size=16),
        xaxis=dict(
            title_font=dict(size=15),
            tickfont=dict(size=16),
        ),
        yaxis=dict(
            title_font=dict(size=18),
            tickfont=dict(size=16),
        ),
        legend=dict(
            title_font=dict(size=16),
            font=dict(size=14),
        ),
    )

def section_header(text: str) -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <h2>{text}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

def apply_temperature_axis_colors(fig) -> None:
    fig.update_xaxes(
        tickvals=["Low Temp", "Mid Temp", "High Temp"],
        ticktext=[
            "<span style='color:#22C55E'><b>Low Temp</b></span>",
            "<span style='color:#FACC15'><b>Mid Temp</b></span>",
            "<span style='color:#EF4444'><b>High Temp</b></span>",
        ],
    )

def main() -> None:
    st.set_page_config(
        page_title="LLM Temperature Stability Dashboard",
        layout="wide",
    )

    st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.03em;
    }
    
    h2, h3 {
    text-align: center;
    }

    /* Main dashboard title */
    h1 {
        text-align: center;
        font-size: 4rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.25rem;
        /* Subtle royal-blue outline/glow */
        text-shadow:
          1px 0 0 rgba(37, 99, 235, 0.5),
            -1px 0 0 rgba(37, 99, 235, 0.5),
            0 1px 0 rgba(37, 99, 235, 0.5),
            0 -1px 0 rgba(37, 99, 235, 0.5),
            1px 1px 0 rgba(37, 99, 235, 0.5),
            -1px -1px 0 rgba(37, 99, 235, 0.5),
            1px -1px 0 rgba(37, 99, 235, 0.5),
            -1px 1px 0 rgba(37, 99, 235, 0.5); 
    }

    /* Subtitle / caption */
    [data-testid="stCaptionContainer"] {
        text-align: center;
        font-size: 1.1rem;
        color: #9CA3AF;
        margin-bottom: 2rem;
    }

    /* KPI Card Container */
    [data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #243244;
        padding: 1.25rem;
        border-radius: 1rem;
    }

    [data-testid="stMetricLabel"] > div {
    font-size: 1.3rem;
    font-weight: 700 !important;
    color: #e5e7eb;
    }

    [data-testid="stMetricValue"] > div {
        font-size: 2.2rem;
        font-weight: 400 !important;
        color: #ffffff;
    }

    .section-header {
    background-color: #111827;
    border: 5px solid #243244;
    border-radius: 1rem;
    padding: 0.75rem 1.5rem;
    margin: 2rem 0 1.5rem 0;
    text-align: center;
    }

    .section-header h2 {
        margin: 0;
        color: #e5e7eb;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.03em;
    }

    /* Conclusion Box */
    .insight-box {
        background-color: #111827;
        border: 5px solid #243244;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-top: 1rem;
        color: #e5e7eb;
        line-height: 1.7;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )

    df = load_data()

    st.title("LLM Temperature Stability Dashboard")
    st.caption(
        "Visual analytics for a controlled LLM pipeline experiment across temperature profiles."
    )

    total_runs = len(df)
    success_rate = (df["status"].eq("success").mean()) * 100
    conditions = df.groupby(["experiment_id", "temperature_profile"]).ngroups
    total_reasks = int(df["reask_count"].sum())
    total_retries = int(df["failures_total"].sum())
    total_errors = int(df["has_error"].sum())

    section_header("Operational Reliability")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Runs", f"{total_runs}")
    col2.metric("Success Rate", f"{success_rate:.1f}%")
    col3.metric("Experimental Conditions", f"{conditions}")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Reasks", f"{total_reasks}")
    col2.metric("Total Retries", f"{total_retries}")
    col3.metric("Total Errors", f"{total_errors}")

    st.divider()

    section_header("Temperature Evaluation")

    grouped = (
        df.groupby(["experiment_label", "profile_label"], as_index=False)
        .agg(
            avg_grade=("grade", "mean"),
            avg_confidence=("score_confidence", "mean"),
        )
    )

    left, right = st.columns(2)

    with left:
        fig_grade = px.bar(
            grouped,
            x="profile_label",
            y="avg_grade",
            color="experiment_label",
            barmode="group",
            title="Average Grade by Temperature Profile",
            labels={
                "profile_label": "",
                "avg_grade": "Avg. Grade",
                "experiment_label": "Experiment",
            },
            category_orders={"profile_label": PROFILE_ORDER},
            color_discrete_map=COLOR_MAP,
        )

        apply_outline_style(fig_grade)
        apply_chart_theme(fig_grade)
        apply_temperature_axis_colors(fig_grade)
        

        st.plotly_chart(fig_grade, use_container_width=True)

    with right:
        fig_conf = px.bar(
            grouped,
            x="profile_label",
            y="avg_confidence",
            color="experiment_label",
            barmode="group",
            title="Average Confidence by Temperature Profile",
            labels={
                "profile_label": "",
                "avg_confidence": "Avg. Confidence",
                "experiment_label": "Experiment",
            },
            category_orders={"profile_label": PROFILE_ORDER},
            color_discrete_map=COLOR_MAP,
        )

        apply_outline_style(fig_conf)
        apply_chart_theme(fig_conf)
        apply_temperature_axis_colors(fig_conf)

        st.plotly_chart(fig_conf, use_container_width=True)

    st.divider()

    section_header("Fixed vs Variable Evaluation")

    experiment_summary = (
        df.groupby("experiment_label", as_index=False)
        .agg(
            avg_grade=("grade", "mean"),
            avg_confidence=("score_confidence", "mean"),
        )
    )

    left, right = st.columns(2)

    with left:
        fig_eval_grade = px.bar(
            experiment_summary,
            x="experiment_label",
            y="avg_grade",
            color="experiment_label",
            title="Average Grade by Evaluation Type",
            labels={
                "experiment_label": "",
                "avg_grade": "Avg. Grade",
            },
            color_discrete_map=COLOR_MAP,
        )

        apply_outline_style(fig_eval_grade)
        fig_eval_grade.update_traces(width=0.4)
        apply_chart_theme(fig_eval_grade)

        st.plotly_chart(fig_eval_grade, use_container_width=True)

    with right:
        fig_eval_conf = px.bar(
            experiment_summary,
            x="experiment_label",
            y="avg_confidence",
            color="experiment_label",
            title="Average Confidence by Evaluation Type",
            labels={
                "experiment_label": "",
                "avg_confidence": "Avg. Confidence",
            },
            color_discrete_map=COLOR_MAP,
        )

        apply_outline_style(fig_eval_conf)
        fig_eval_conf.update_traces(width=0.4)
        apply_chart_theme(fig_eval_conf)

        st.plotly_chart(fig_eval_conf, use_container_width=True)

    st.markdown(
    """
    <div class="insight-box">
    <h3>Conclusion</h3>
    <p>
    Across 300 controlled runs, temperature had minimal observed impact on
    pipeline reliability, grading, or confidence. More testing will be
    needed to confirm, but I believe this was the outcome for two 
    reasons.

    Firstly, the system_prompts passed to the AI are highly constrained
    and focused, which is good practice in design, as evident from 
    the pipeline stability shown in this experiment, but I think
    strong system prompts highly mitigate much of the effects of 
    llm temperature increases, even at large values.

    Further, I believe the pipeline itself produces results that are 
    highly deterministic and schema-validated. The actual outputs
    themselves do not leave a lot of room for non-absolute 
    determination, which I think is precisely where you would see
    the greatest effect of temperature. 
    </p>
    </div>
    """,
    unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()