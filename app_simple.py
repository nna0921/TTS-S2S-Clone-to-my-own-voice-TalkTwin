import PyPDF2
from gtts import gTTS
from pydub import AudioSegment
import re
import os
import streamlit as st
import tempfile

CHUNK_SIZE = 2000
TEMP_DIR = "chunks1"

SPEAKERS = {
    "en": "English (Default)",
    "en-us": "English (US)", 
    "en-uk": "English (UK)",
    "en-au": "English (Australia)",
    "en-ca": "English (Canada)"
}

def clean_text(text):
    text = text.replace("—", "-")
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")
    text = re.sub(r"(Scan to Download\s*)+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s-\s", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text, max_chars=CHUNK_SIZE):
    chunks = []
    while len(text) > max_chars:
        split_at = text.rfind(" ", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunks.append(text[:split_at])
        text = text[split_at:]
    if text:
        chunks.append(text)
    return chunks

def merge_audio(files, output_file):
    combined = AudioSegment.empty()
    for f in files:
        combined += AudioSegment.from_wav(f)
    combined.export(output_file, format="wav")
    return output_file

st.set_page_config(page_title="TalkTwin", page_icon="🗣️", layout="wide")

# Load CSS if available
try:
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    with open(css_path, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("CSS file not found. Using default styling.")

# Deployment notice
if 'STREAMLIT_CLOUD' in os.environ or 'STREAMLIT_SHARING' in os.environ:
    st.info("🚀 Running on Streamlit Cloud! First-time model loading may take a few minutes.")

logo_path = os.path.join(os.path.dirname(__file__), "talktwin_logo.png")

if os.path.exists(logo_path):
    import base64
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <div class="talktwin-header">
        <img src="data:image/png;base64,{logo_base64}" alt="TalkTwin Logo"/>
        <h1>TalkTwin</h1>
    </div>
    <p class="talktwin-tagline">
        Transform your PDFs into captivating audio with customizable voices!
    </p>
    """, unsafe_allow_html=True)
else:
    st.title("🗣️ TalkTwin")
    st.markdown("Transform your PDFs into captivating audio with customizable voices!")

st.header("Upload Your PDF")
pdf_file = st.file_uploader("Choose a PDF file", type=["pdf"], help="Upload a PDF to convert its text to speech.")

if pdf_file:
    st.header("Choose a Voice")
    selected_speaker = st.selectbox(
        "Select voice language/accent:",
        options=list(SPEAKERS.keys()),
        format_func=lambda x: SPEAKERS[x],
        help="Choose from different English accents and regions."
    )

    if st.button("🎙️ Generate Audio", type="primary"):
        # Create directories
        os.makedirs(TEMP_DIR, exist_ok=True)
            
        with st.spinner("Extracting text and generating audio..."):
            reader = PyPDF2.PdfReader(pdf_file)
            full_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            full_text = clean_text(full_text)
            text_chunks = chunk_text(full_text)

            progress_bar = st.progress(0)
            status_text = st.empty()
            chunk_files = []
            
            for i, chunk in enumerate(text_chunks):
                status_text.text(f"Processing chunk {i+1}/{len(text_chunks)}...")
                filename = os.path.join(TEMP_DIR, f"chunk_{i}.wav")
                
                # Generate audio using gTTS
                try:
                    tts = gTTS(text=chunk, lang=selected_speaker, slow=False)
                    tts.save(filename)
                    chunk_files.append(filename)
                except Exception as e:
                    st.error(f"Error generating audio for chunk {i+1}: {str(e)}")
                    continue
                    
                progress_bar.progress((i + 1) / len(text_chunks))

            base_audio = f"{os.path.splitext(pdf_file.name)[0]}_base.wav"
            merge_audio(chunk_files, base_audio)

        st.success("Audio generated successfully!")
        st.audio(base_audio)

        with open(base_audio, "rb") as f:
            st.download_button(
                label="📥 Download Full Audio",
                data=f,
                file_name=base_audio,
                mime="audio/wav"
            )

        st.session_state.chunk_files = chunk_files
        st.session_state.base_audio = base_audio
        st.session_state.pdf_name = pdf_file.name

if "base_audio" in st.session_state:
    st.markdown("---")
    st.header("🎉 Audio Generated Successfully!")
    st.info("Your PDF has been converted to speech! You can play it above or download it.")
    st.info("💡 **Note**: This simplified version uses Google Text-to-Speech for reliable deployment on Streamlit Cloud.")
