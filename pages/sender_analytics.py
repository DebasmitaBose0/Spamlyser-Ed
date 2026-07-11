"""Sender reputation analytics dashboard for Spamlyser Pro.

Provides detailed insights into sender behavior, reputation scoring,
and threat pattern analysis across all tracked senders.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def render_sender_analytics():
    st.markdown("# 📊 Sender Reputation Analytics")
    st.markdown("Analyze sender behavior, reputation trends, and threat patterns.")

    reputation = st.session_state.get("sender_reputation")
    if reputation is None:
        st.warning("Sender reputation module is not initialized.")
        return

    senders = reputation.get_top_spam_senders(limit=100)
    if not senders:
        st.info(
            "No sender data available yet. "
            "Messages will be tracked automatically as you analyze SMS content."
        )
        return

    df = pd.DataFrame(senders)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Senders Tracked", len(df))
    kpi2.metric(
        "Avg Reputation Score",
        f"{df['reputation_score'].mean():.2f}" if not df.empty else "N/A",
    )
    kpi3.metric("Total Spam Messages", int(df["spam_count"].sum()))
    kpi4.metric("Total Messages Analyzed", int(df["total_messages"].sum()))

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Sender Rankings", "Threat Heatmap", "Sender Details", "Trend Analysis"]
    )

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            top_n = st.slider(
                "Number of senders to display",
                min_value=5,
                max_value=min(50, len(df)),
                value=min(15, len(df)),
            )
            sorted_df = df.sort_values("spam_count", ascending=False).head(top_n)
            fig = px.bar(
                sorted_df,
                x="sender",
                y="spam_count",
                color="reputation_score",
                color_continuous_scale="RdYlGn_r",
                title=f"Top {top_n} Spam Senders by Message Count",
                labels={
                    "sender": "Sender",
                    "spam_count": "Spam Messages",
                    "reputation_score": "Reputation Score",
                },
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig_pie = px.pie(
                df.head(10),
                values="spam_count",
                names="sender",
                title="Spam Distribution Top 10",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        pivot = df.pivot_table(
            values="spam_count",
            index="sender",
            columns="reputation_score",
            aggfunc="sum",
        ).fillna(0)
        if not pivot.empty:
            st.write("**Sender vs Reputation Score Heatmap**")
            st.dataframe(pivot.style.background_gradient(cmap="YlOrRd"), height=400)
        else:
            st.info("Not enough data for heatmap visualization.")

    with tab3:
        selected_sender = st.selectbox(
            "Select a sender to view details",
            df["sender"].tolist(),
        )
        if selected_sender:
            sender_data = reputation.get_reputation(selected_sender)
            if sender_data:
                cols = st.columns(3)
                cols[0].metric(
                    "Reputation Score",
                    f"{sender_data['reputation_score']:.3f}",
                    delta=(
                        "Good"
                        if sender_data["reputation_score"] > 0.7
                        else "Poor" if sender_data["reputation_score"] < 0.3
                        else "Average"
                    ),
                )
                cols[1].metric(
                    "Total Messages", sender_data["total_messages"]
                )
                cols[2].metric(
                    "Spam Ratio",
                    f"{(sender_data['spam_count'] / sender_data['total_messages'] * 100):.1f}%"
                    if sender_data["total_messages"] > 0
                    else "0%",
                )
                details = {
                    "Sender": selected_sender,
                    "First Seen": sender_data.get("first_seen", "N/A"),
                    "Last Seen": sender_data.get("last_seen", "N/A"),
                    "Spam Count": sender_data["spam_count"],
                    "Ham Count": sender_data["ham_count"],
                    "Threat Types": ", ".join(
                        f"{k}: {v}"
                        for k, v in sender_data.get("threat_types", {}).items()
                    ),
                }
                st.json(details)

    with tab4:
        st.write("**Reputation Score Distribution**")
        fig_hist = px.histogram(
            df,
            x="reputation_score",
            nbins=20,
            title="Distribution of Sender Reputation Scores",
            labels={"reputation_score": "Reputation Score", "count": "Number of Senders"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        st.write("**Message Volume by Sender**")
        fig_scatter = px.scatter(
            df,
            x="total_messages",
            y="spam_count",
            size="spam_count",
            hover_name="sender",
            color="reputation_score",
            color_continuous_scale="RdYlGn_r",
            title="Message Volume vs Spam Activity",
            labels={
                "total_messages": "Total Messages",
                "spam_count": "Spam Count",
            },
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    st.caption(
        "Reputation scores range from 0.0 (high-risk spammer) to 1.0 (trusted sender). "
        "Scores are calculated based on spam ratio, confidence scores, and threat type diversity."
    )


if __name__ == "__main__":
    render_sender_analytics()
