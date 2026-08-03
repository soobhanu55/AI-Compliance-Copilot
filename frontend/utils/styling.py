import streamlit as st

# Single accent color + restrained neutrals — avoid Streamlit's default blue.
ACCENT = "#1F6F5C"  # muted teal-green — reads as "compliance/trust", not generic SaaS blue
NEUTRAL_BG = "#0E1116"
NEUTRAL_SURFACE = "#161B22"
NEUTRAL_TEXT = "#E6E8EB"
NEUTRAL_MUTED = "#8B949E"

CUSTOM_CSS = f"""
<style>
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .stApp {{
        background-color: {NEUTRAL_BG};
        color: {NEUTRAL_TEXT};
    }}

    section[data-testid="stSidebar"] {{
        background-color: {NEUTRAL_SURFACE};
        border-right: 1px solid rgba(255,255,255,0.06);
    }}

    .stButton > button {{
        background-color: {ACCENT};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.25rem;
        font-weight: 500;
    }}
    .stButton > button:hover {{
        background-color: {ACCENT}cc;
    }}

    div[data-testid="stMetric"] {{
        background-color: {NEUTRAL_SURFACE};
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.06);
    }}

    h1, h2, h3 {{
        color: {NEUTRAL_TEXT};
        font-weight: 600;
    }}

    .muted {{
        color: {NEUTRAL_MUTED};
        font-size: 0.9rem;
    }}
</style>
"""


def apply_custom_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
