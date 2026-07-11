"""SMS encoding and character analysis page for Spamlyser Pro."""

import streamlit as st
import plotly.express as px
import pandas as pd


def render_encoding_analysis():
    st.markdown("# 🔤 SMS Encoding & Character Analysis")
    st.markdown(
        "Detect encoding obfuscation, suspicious Unicode, and character-level anomalies "
        "in SMS messages."
    )

    try:
        from models.encoding_analyzer import analyze_message_complexity
    except ImportError:
        st.warning("Encoding analyzer module not available.")
        return

    sample = st.text_area(
        "Enter an SMS message to analyze",
        height=150,
        placeholder="Paste an SMS message here to analyze its encoding and character patterns...",
        help="The analyzer will detect encoding techniques, Unicode categories, and suspicious characters.",
    )

    if st.button("🔍 Analyze Encoding", type="primary", use_container_width=True):
        if not sample.strip():
            st.warning("Please enter a message to analyze.")
            return

        with st.spinner("Analyzing character encoding..."):
            result = analyze_message_complexity(sample)

        score = result["complexity_score"]
        risk = result["risk_level"]
        color_map = {"none": "green", "low": "yellow", "medium": "orange", "high": "red"}
        st.markdown(
            f"### Complexity Score: **{score}** "
            f"(:{color_map[risk]}[{risk.upper()} risk])"
        )

        tab1, tab2, tab3 = st.tabs(
            ["Character Distribution", "Encoding Detection", "Suspicious Characters"]
        )

        with tab1:
            dist = result["details"]["char_distribution"]
            if dist:
                df = pd.DataFrame(
                    {"Category": list(dist.keys()), "Count": list(dist.values())}
                )
                fig = px.pie(
                    df,
                    names="Category",
                    values="Count",
                    title="Character Category Distribution",
                )
                st.plotly_chart(fig, use_container_width=True)

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Characters", result["details"]["total_chars"])
                col2.metric("Non-ASCII", result["details"]["non_ascii_chars"])
                col3.metric("ASCII Ratio", f"{result['details']['ascii_ratio']:.1%}")

        with tab2:
            encodings = result["details"].get("encodings_found", [])
            if encodings:
                st.warning(
                    f"Detected {len(encodings)} encoding technique(s): "
                    f"{', '.join(encodings)}"
                )
                for enc in encodings:
                    st.markdown(f"- **{enc}**: May indicate obfuscation attempt")
            else:
                st.success("No encoding obfuscation techniques detected.")

        with tab3:
            susp = result["details"].get("suspicious_categories", [])
            if susp:
                st.warning(
                    f"Found {result['details']['suspicious_unicode_spans']} "
                    f"suspicious Unicode character(s) in {len(susp)} categories."
                )
                for cat in susp:
                    st.markdown(f"- **{cat}**: Characters that may bypass text filters")
            else:
                st.success("No suspicious Unicode characters detected.")

        with st.expander("📋 Full Analysis Details"):
            st.json(result)

    st.markdown("---")
    st.caption(
        "Encoding analysis helps detect obfuscated spam that uses Unicode homoglyphs, "
        "zero-width characters, or encoded payloads to bypass text-based filters."
    )


if __name__ == "__main__":
    render_encoding_analysis()
