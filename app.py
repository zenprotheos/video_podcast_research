import time

import streamlit as st


def _render_loader(duration: float = 1.2, message: str = "Loading the transcript magic..."):
    placeholder = st.empty()
    loader_html_template = """
<div class="loader-wrapper">
  <div class="loader-face">
    <div class="eyes">
      <span></span>
      <span></span>
    </div>
    <div class="smile"></div>
  </div>
  <div class="loader-bubbles">
    <span></span>
    <span></span>
    <span></span>
  </div>
  <p class="loader-message">{message}</p>
</div>
<style>
.loader-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1.75rem 2rem;
  border-radius: 1.5rem;
  background: linear-gradient(135deg, #0f172a, #1e293b);
  color: #e0f2fe;
  max-width: 340px;
  margin: 1.5rem auto 2rem auto;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.35);
}
.loader-face {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #38bdf8, #60a5fa);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 -12px 30px rgba(15, 23, 42, 0.35);
}
.loader-face .eyes {
  position: absolute;
  top: 32px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  padding: 0 34px;
}
.loader-face .eyes span {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.8);
  animation: blink 2.8s ease-in-out infinite;
}
.loader-face .smile {
  position: absolute;
  bottom: 24px;
  left: 50%;
  width: 50px;
  height: 28px;
  border-bottom: 4px solid #fff;
  border-radius: 0 0 80px 80px;
  transform: translateX(-50%);
}
.loader-bubbles {
  display: flex;
  gap: 0.6rem;
}
.loader-bubbles span {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #38bdf8;
  animation: bounce 1.2s ease-in-out infinite;
}
.loader-bubbles span:nth-child(2) {
  animation-delay: 0.15s;
}
.loader-bubbles span:nth-child(3) {
  animation-delay: 0.3s;
}
.loader-message {
  font-size: 0.95rem;
  margin: 0;
  color: #bae6fd;
  text-align: center;
}
@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
}
@keyframes blink {
  0%, 20%, 100% {
    height: 18px;
  }
  10% {
    height: 5px;
  }
}
</style>
"""
    loader_html = loader_html_template.replace("{message}", message)
    placeholder.markdown(loader_html, unsafe_allow_html=True)
    time.sleep(duration)
    placeholder.empty()


st.set_page_config(page_title="Bulk Transcribe", layout="wide")

if not st.session_state.get("main_menu_loader_shown", False):
    _render_loader(message="Preparing the Bulk Transcribe lobby...")
    st.session_state["main_menu_loader_shown"] = True

st.title("Bulk Transcribe - Main Menu")
st.markdown("Navigate to:")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/01_YouTube_Search.py", label="🔍 YouTube Search",
                 help="Search YouTube and select videos for transcription")

with col2:
    st.page_link("pages/02_Bulk_Transcribe.py", label="📝 Bulk Transcribe - Transcript Tool",
                 help="Process YouTube URLs and MP3 links to generate transcripts")


