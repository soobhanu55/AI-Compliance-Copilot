import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import create_gap_report
from utils.styling import ACCENT, apply_custom_theme

st.set_page_config(page_title="Gap Report — AI Compliance Copilot", page_icon="\U0001f4cb", layout="wide")
apply_custom_theme()

st.title("Compliance Gap Report")

with st.form("company_profile"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Company name", "Acme Logistics GmbH")
        sector = st.text_input("Sector", "Logistics software")
        employee_count = st.number_input("Employee count", min_value=1, value=45)
    with col2:
        uses_ai = st.checkbox("Uses AI systems", value=True)
        ai_systems = st.text_area("AI system descriptions (one per line)", "Route optimization model")
        vendors = st.text_area("Third-party vendors (one per line)", "")

    submitted = st.form_submit_button("Generate gap report")

if submitted:
    profile = {
        "name": name,
        "sector": sector,
        "employee_count": employee_count,
        "uses_ai_systems": uses_ai,
        "ai_system_descriptions": [s for s in ai_systems.splitlines() if s.strip()],
        "third_party_vendors": [v for v in vendors.splitlines() if v.strip()],
        "notes": "",
    }

    with st.status("Generating report...", expanded=True) as status:
        st.write("Retrieving regulation text → classifying relevance → drafting summary...")
        try:
            report = create_gap_report(st.session_state.get("user_id", "demo-user"), profile)
            status.update(label="Report ready", state="complete")
        except Exception as exc:
            status.update(label="Backend unavailable", state="error")
            st.error(f"Could not reach backend at BACKEND_URL: {exc}")
            st.stop()

    assessments = report["assessments"]
    if assessments:
        df = pd.DataFrame(assessments)
        counts = df["verdict"].value_counts().reset_index()
        counts.columns = ["verdict", "count"]

        fig = px.bar(
            counts,
            x="verdict",
            y="count",
            color="verdict",
            color_discrete_sequence=[ACCENT, "#8B949E", "#C97B4A"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E6E8EB",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No regulation clauses retrieved — has the regulation corpus been indexed yet?")
