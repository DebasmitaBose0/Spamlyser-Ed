import streamlit as st
import plotly.express as px
import pandas as pd
from models.drift_tracker import ModelDriftTracker

def render_drift_dashboard():
    st.title("📉 Model Drift & Statistical Stability Dashboard")
    st.markdown("""
    Monitor prediction distribution shifts and accuracy decay over time. 
    Uses **Population Stability Index (PSI)** and **Kullback-Leibler (KL) Divergence** to flag model decay.
    """)

    tracker = ModelDriftTracker()

    if not tracker.history:
        st.info("No historical model evaluations registered. Run model benchmarks to generate drift logs.")
        # Seed dummy data for preview/demonstration
        if st.button("🌱 Seed Sample Drift Log Data"):
            tracker.record_evaluation(0.94, [0.88, 0.12], [0.90, 0.10])
            tracker.record_evaluation(0.92, [0.85, 0.15], [0.90, 0.10])
            tracker.record_evaluation(0.88, [0.78, 0.22], [0.90, 0.10])
            st.success("Sample drift history seeded!")
            st.rerun()
        return

    df = pd.DataFrame(tracker.history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    latest = tracker.history[-1]
    
    # Summary Metrics Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Current Accuracy", 
            value=f"{latest['accuracy'] * 100:.1f}%", 
            delta=f"-{latest['accuracy_drift'] * 100:.1f}%" if latest['accuracy_drift'] > 0 else "0.0%"
        )
    with col2:
        st.metric(
            label="Population Stability Index (PSI)", 
            value=latest["psi"],
            delta="Warning" if latest["psi"] > 0.1 else "Healthy",
            delta_color="inverse" if latest["psi"] > 0.1 else "normal"
        )
    with col3:
        st.metric(
            label="KL Divergence", 
            value=latest["kl_divergence"]
        )

    # Status Notification Box
    if latest["psi"] > 0.25:
        st.error(f"🚨 **Critical Action Required:** High prediction drift detected (PSI = {latest['psi']}). Consider retraining the ensemble classifiers.")
    elif latest["psi"] > 0.1:
        st.warning(f"⚠️ **Warning:** Mild prediction drift detected (PSI = {latest['psi']}). Monitor validation datasets.")
    else:
        st.success("✅ **Model Performance Stable:** Statistical distributions are within expected baseline limits.")

    st.markdown("---")

    # Chart 1: Accuracy & Drift Timeline
    st.subheader("📈 Accuracy Performance & Decay Timeline")
    fig_acc = px.line(
        df, 
        x="timestamp", 
        y=["accuracy", "accuracy_drift"], 
        labels={"value": "Score", "timestamp": "Evaluation Date"},
        title="Accuracy vs. Cumulative Drift Decay Rate"
    )
    st.plotly_chart(fig_acc, use_container_width=True)

    # Chart 2: Statistical Divergence Metrics
    st.subheader("📊 Statistical Divergence (PSI vs. KL Divergence)")
    fig_div = px.bar(
        df,
        x="timestamp",
        y=["psi", "kl_divergence"],
        barmode="group",
        title="PSI & KL Divergence Distribution Shifts"
    )
    st.plotly_chart(fig_div, use_container_width=True)

    # Data Table
    st.subheader("📋 Detailed History Log")
    st.dataframe(df.sort_values(by="timestamp", ascending=False), use_container_width=True)

render_drift_dashboard()
