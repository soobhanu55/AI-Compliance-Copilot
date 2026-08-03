import streamlit as st

from utils.api_client import upload_document
from utils.styling import apply_custom_theme

st.set_page_config(page_title="Upload — AI Compliance Copilot", page_icon="\U0001f4c1", layout="wide")
apply_custom_theme()

st.title("Upload Company Documents")
st.markdown("Upload internal policies, data flow diagrams, AI system descriptions, or existing certifications.")

doc_type = st.selectbox("Document type", ["company_policy", "regulation"], index=0)
uploaded_files = st.file_uploader(
    "PDF, DOCX, or TXT", type=["pdf", "docx", "txt"], accept_multiple_files=True
)

if uploaded_files and st.button("Index documents"):
    user_id = st.session_state.get("user_id", "demo-user")
    for file in uploaded_files:
        with st.status(f"Indexing {file.name}...", expanded=True) as status:
            st.write("Parsing → chunking → embedding → storing in Supabase...")
            try:
                result = upload_document(user_id, doc_type, file)
                status.update(
                    label=f"Indexed {file.name} ({result['chunks_indexed']} chunks)",
                    state="complete",
                )
            except Exception as exc:
                status.update(label=f"Failed: {file.name}", state="error")
                st.error(str(exc))
