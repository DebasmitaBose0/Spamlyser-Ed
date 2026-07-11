"""Webhook monitoring dashboard for Spamlyser Pro.

Provides real-time visibility into webhook delivery status,
history logs, and aggregate delivery statistics.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, UTC


def render_webhook_dashboard():
    st.markdown("# 🔔 Webhook Delivery Dashboard")
    st.markdown("Monitor real-time webhook notifications and delivery status.")

    notifier = st.session_state.get("webhook_notifier")
    if notifier is None:
        st.warning("Webhook system is not initialized.")
        return

    stats = notifier.get_delivery_stats()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Deliveries", stats["total_deliveries"])
    kpi2.metric("Successful", stats["successful"])
    kpi3.metric("Failed", stats["failed"])
    kpi4.metric("Success Rate", f"{stats['success_rate']:.1f}%")

    with st.expander("📊 Per-Webhook Statistics", expanded=True):
        if stats["by_webhook"]:
            rows = []
            for url, data in stats["by_webhook"].items():
                rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
                rows.append({
                    "Webhook URL": url,
                    "Total": data["total"],
                    "Success": data["success"],
                    "Failed": data["failed"],
                    "Skipped": data["skipped"],
                    "Rate": f"{rate:.1f}%",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No delivery data yet. Send a spam detection to generate statistics.")

    with st.expander("📋 Recent Delivery History", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.selectbox(
                "Filter by status", ["All", "success", "failed", "skipped"],
                key="wh_filter_status",
            )
        with col2:
            history = notifier.get_history(limit=200)
            total_entries = len(history)
            st.markdown(f"**{total_entries}** entries in history")

        status_map = {"All": None, "success": "success", "failed": "failed", "skipped": "skipped"}
        filtered = notifier.get_history(
            limit=200,
            status=status_map[filter_status],
        )

        if filtered:
            rows = []
            for entry in reversed(filtered):
                ts = entry.get("timestamp", "")[:19]
                status = entry.get("status", "unknown")
                icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
                rows.append({
                    "Time": ts,
                    "Status": f"{icon} {status}",
                    "Webhook": entry.get("webhook_url", ""),
                    "Event": entry.get("event", ""),
                    "Attempt": entry.get("attempt", "-"),
                    "Error": (entry.get("error", "") or "")[:80],
                })
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Error": st.column_config.TextColumn(width="large"),
                },
            )

            if st.button("🗑️ Clear History", type="secondary"):
                notifier.clear_history()
                st.rerun()
        else:
            st.info("No webhook activity recorded yet.")

    with st.expander("⚙️ Webhook Endpoints"):
        webhooks = notifier.get_webhooks()
        if webhooks:
            for i, wh in enumerate(webhooks):
                cols = st.columns([3, 1, 1, 1])
                status_icon = "✅" if wh.get("enabled", True) else "⛔"
                cols[0].markdown(
                    f"{status_icon} **{wh.get('label', wh['url'])}** — `{wh['url']}`"
                )
                cols[1].markdown(
                    f"Events: {', '.join(wh.get('events', ['spam_detected']))}"
                )
                if cols[2].button("Toggle", key=f"toggle_wh_{i}"):
                    notifier.update_webhook(
                        wh["url"], {"enabled": not wh.get("enabled", True)}
                    )
                    st.rerun()
                if cols[3].button("Remove", key=f"del_wh_dash_{i}"):
                    notifier.remove_webhook(wh["url"])
                    st.rerun()
        else:
            st.info("No webhooks configured. Go to Settings to add one.")

    st.markdown("---")
    st.caption(
        "Webhook deliveries are sent asynchronously with exponential backoff retry. "
        "The circuit breaker automatically disables endpoints after repeated failures."
    )


if __name__ == "__main__":
    render_webhook_dashboard()
