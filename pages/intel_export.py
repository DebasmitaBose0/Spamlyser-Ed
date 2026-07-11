"""Threat intelligence export page for Spamlyser Pro."""

import streamlit as st
from datetime import datetime
from pathlib import Path


def render_intel_export():
    st.markdown("# 🛡️ Threat Intelligence Export")
    st.markdown(
        "Export classification results in industry-standard formats for "
        "sharing with security teams and SIEM integration."
    )

    try:
        from models.threat_intel_exporter import (
            export_as_stix_bundle,
            export_as_csv,
            export_as_json_report,
        )
    except ImportError:
        st.warning("Threat intelligence exporter module not available.")
        return

    history = st.session_state.get("ensemble_history", [])
    if not history:
        st.info(
            "No classification history available. "
            "Analyze some SMS messages first to generate export data."
        )
        return

    st.success(f"**{len(history)}** classification records available for export.")

    tab1, tab2, tab3 = st.tabs(["STIX 2.1 Bundle", "CSV (SIEM)", "JSON Report"])

    fmt = "%Y%m%d_%H%M%S"
    now = datetime.now().strftime(fmt)

    with tab1:
        st.markdown(
            "**STIX 2.1** is the industry standard for cyber threat intelligence "
            "sharing. The bundle includes observations and indicators."
        )
        if st.button("Generate STIX Bundle", key="stix_gen", use_container_width=True):
            with st.spinner("Generating STIX 2.1 bundle..."):
                stix_data = export_as_stix_bundle(history)
            st.download_button(
                "📥 Download STIX Bundle (.json)",
                data=stix_data,
                file_name=f"spamlyser_threat_intel_{now}.json",
                mime="application/json",
            )
            with st.expander("Preview STIX Bundle"):
                st.code(stix_data[:2000], language="json")

    with tab2:
        st.markdown(
            "**CSV format** is compatible with most SIEM platforms "
            "(Splunk, ELK, Sentinel, etc.)."
        )
        if st.button("Generate CSV", key="csv_gen", use_container_width=True):
            with st.spinner("Generating CSV export..."):
                csv_data = export_as_csv(history)
            st.download_button(
                "📥 Download CSV (.csv)",
                data=csv_data,
                file_name=f"spamlyser_siem_export_{now}.csv",
                mime="text/csv",
            )
            with st.expander("Preview CSV"):
                st.code(csv_data[:1000])

    with tab3:
        st.markdown(
            "**JSON report** includes full classification details with "
            "aggregate statistics and threat type breakdown."
        )
        if st.button("Generate JSON Report", key="json_gen", use_container_width=True):
            with st.spinner("Generating JSON report..."):
                json_data = export_as_json_report(history)
            st.download_button(
                "📥 Download JSON Report (.json)",
                data=json_data,
                file_name=f"spamlyser_report_{now}.json",
                mime="application/json",
            )
            with st.expander("Preview JSON Report"):
                st.code(json_data[:2000], language="json")

    st.markdown("---")
    st.caption(
        "All exports are generated from the current session's classification history. "
        "STIX indicators use the `x-spam-classification` custom observable type."
    )


if __name__ == "__main__":
    render_intel_export()
