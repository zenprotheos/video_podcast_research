import streamlit as st

st.set_page_config(page_title="Bulk Transcribe", layout="wide")
st.title("Bulk Transcribe - Main Menu")
st.markdown("Navigate to:")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/01_YouTube_Search.py", label="🔍 YouTube Search",
                 help="Search YouTube and select videos for transcription")

with col2:
    st.page_link("pages/02_Bulk_Transcribe.py", label="📝 Bulk Transcribe - Transcript Tool",
                 help="Process YouTube URLs and MP3 links to generate transcripts")


