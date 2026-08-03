import streamlit as st

from utils.api_client import send_chat_message
from utils.styling import apply_custom_theme

st.set_page_config(page_title="Chat — AI Compliance Copilot", page_icon="\U0001f4ac", layout="wide")
apply_custom_theme()

st.title("Compliance Assistant")

language = st.radio("Language / Sprache", ["en", "de"], horizontal=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for citation in msg.get("citations", []):
            st.caption(f"{citation['regulation']} {citation['article']}")

if prompt := st.chat_input("Ask e.g. \"Does the AI Act apply to our routing algorithm?\""):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=True) as status:
            st.write("Retrieving regulation text → company documents...")
            try:
                result = send_chat_message(
                    user_id=st.session_state.get("user_id", "demo-user"),
                    message=prompt,
                    language=language,
                )
                status.update(label="Done", state="complete")
            except Exception as exc:
                status.update(label="Backend unavailable", state="error")
                st.error(f"Could not reach backend at BACKEND_URL: {exc}")
                st.stop()

        st.markdown(result["answer"])
        for citation in result["citations"]:
            st.caption(f"{citation['regulation']} {citation['article']} — {citation['excerpt']}")

        st.session_state.messages.append(
            {"role": "assistant", "content": result["answer"], "citations": result["citations"]}
        )
