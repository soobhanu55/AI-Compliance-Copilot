import streamlit as st
from streamlit_option_menu import option_menu

from utils.styling import apply_custom_theme

st.set_page_config(
    page_title="AI Compliance Copilot",
    page_icon="\U0001f4cb",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_theme()

with st.sidebar:
    st.markdown("### AI Compliance Copilot")
    st.markdown('<span class="muted">EU AI Act · NIS2 · CSRD</span>', unsafe_allow_html=True)
    st.divider()
    selected = option_menu(
        menu_title=None,
        options=["Chat", "Upload Documents", "Gap Report"],
        icons=["chat-dots", "cloud-upload", "clipboard-check"],
        default_index=0,
    )

st.title("Welcome")
st.markdown(
    "Use the sidebar to chat with the compliance assistant, upload company documents, "
    "or generate a gap report against the AI Act, NIS2, and CSRD.\n\n"
    "This is a proof-of-concept — not a substitute for legal advice. "
    "See individual pages under `frontend/pages/` for each workflow."
)

st.info(
    f"Navigate via the sidebar. Selected: **{selected}** "
    "(full page routing lives in `frontend/pages/`)."
)
