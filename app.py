import PyPDF2
from TTS.api import TTS
from pydub import AudioSegment
import re
import os
import streamlit as st

# --- Configuration ---
CHUNK_SIZE = 2000
TEMP_DIR = "chunks1"
OUTPUT_DIR = "output_chunks"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Initialize TTS models ---
tts_base = TTS(model_name="tts_models/en/vctk/vits")  # Base TTS model
tts_clone = TTS("voice_conversion_models/multilingual/vctk/freevc24")  # Voice cloning

# Speaker options with gender and accent
SPEAKERS = {
    "p225": "Female - English",
    "p227": "Female - Northern English",
    "p228": "Female - Scottish",
    "p230": "Male - English",
    "p236": "Male - Scottish"
}

# --- Helpers ---
def clean_text(text):
    text = text.replace("—", "-")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
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

# --- Streamlit UI ---
st.set_page_config(page_title="TalkTwin", page_icon="🗣️", layout="wide")

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(css_path, "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- Logo + Title + Tagline Section ---
logo_path = os.path.join(os.path.dirname(__file__), "talktwin_logo.png")

if os.path.exists(logo_path):
    # Convert logo to base64 so we can inject it with HTML
    import base64
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <div class="talktwin-header">
        <img src="data:image/png;base64,{logo_base64}" alt="TalkTwin Logo"/>
        <h1>TalkTwin</h1>
    </div>
    <p class="talktwin-tagline">
        Transform your PDFs into captivating audio with customizable voices or twin it with your own voice!
    </p>
    """, unsafe_allow_html=True)
else:
    st.warning("Logo file 'talktwin_logo.png' not found in the app directory.")


# --- PDF Upload Section ---
st.header("Upload Your PDF")
pdf_file = st.file_uploader("Choose a PDF file", type=["pdf"], help="Upload a PDF to convert its text to speech.")

if pdf_file:
    # Speaker Selection
    st.header("Choose a Speaker")
    selected_speaker = st.selectbox(
        "Select voice style :",
        options=list(SPEAKERS.keys()),
        format_func=lambda x: f"{x}: {SPEAKERS[x]}",
        help="Choose from a variety of voices with different accents and genders."
    )

    # Generate Button
    if st.button("🎙️ Generate Audio", type="primary"):
        with st.spinner("Extracting text and generating audio..."):
            # Extract text
            reader = PyPDF2.PdfReader(pdf_file)
            full_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            full_text = clean_text(full_text)
            text_chunks = chunk_text(full_text)

            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            chunk_files = []
            for i, chunk in enumerate(text_chunks):
                status_text.text(f"Processing chunk {i+1}/{len(text_chunks)}...")
                filename = os.path.join(TEMP_DIR, f"chunk_{i}.wav")
                tts_base.tts_to_file(text=chunk, file_path=filename, speaker=selected_speaker)
                chunk_files.append(filename)
                progress_bar.progress((i + 1) / len(text_chunks))

            # Merge base TTS audio
            base_audio = f"{os.path.splitext(pdf_file.name)[0]}_base.wav"
            merge_audio(chunk_files, base_audio)

        st.success("Audio generated successfully!")
        st.audio(base_audio)

        # Download Button
        with open(base_audio, "rb") as f:
            st.download_button(
                label="📥 Download Full Audio",
                data=f,
                file_name=base_audio,
                mime="audio/wav"
            )

        # Store chunk_files and base_audio in session state for cloning
        st.session_state.chunk_files = chunk_files
        st.session_state.base_audio = base_audio
        st.session_state.pdf_name = pdf_file.name

# --- Voice Cloning Section (only after base audio is generated) ---
if "base_audio" in st.session_state:
    st.markdown("---")
    st.header("Clone It In Your Voice (Optional)")
    st.info("Upload a short voice sample to clone the audio in your own voice.")
    voice_file = st.file_uploader(
        "Upload your 15-sec voice sample (WAV)",
        type=["wav"],
        key="clone_upload",
        help="Upload a clear 15-second WAV file of your voice for cloning."
    )

    if voice_file and st.button("🎤 Clone in My Voice", type="primary"):
        with st.spinner("Cloning audio to your voice..."):
            cloned_chunk_files = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            # Save voice_file temporarily to disk
            temp_voice_path = os.path.join(TEMP_DIR, "voice_sample.wav")
            with open(temp_voice_path, "wb") as f:
                f.write(voice_file.read())
            
            for i, chunk_file in enumerate(st.session_state.chunk_files):
                status_text.text(f"Cloning chunk {i+1}/{len(st.session_state.chunk_files)}...")
                output_path = os.path.join(OUTPUT_DIR, f"cloned_{i}.wav")
                tts_clone.voice_conversion_to_file(
                    source_wav=chunk_file,
                    target_wav=temp_voice_path,
                    file_path=output_path
                )
                cloned_chunk_files.append(output_path)
                progress_bar.progress((i + 1) / len(st.session_state.chunk_files))

            # Merge cloned audio
            final_cloned_audio = f"{os.path.splitext(st.session_state.pdf_name)[0]}_my_voice.wav"
            merge_audio(cloned_chunk_files, final_cloned_audio)

        st.success("Cloned audio ready!")
        st.audio(final_cloned_audio)

        # Download Button for Cloned Audio
        with open(final_cloned_audio, "rb") as f:
            st.download_button(
                label="📥 Download Cloned Audio",
                data=f,
                file_name=final_cloned_audio,
                mime="audio/wav"
            )
           
    