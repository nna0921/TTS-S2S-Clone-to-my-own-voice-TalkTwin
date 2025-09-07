# TalkTwin 🗣️

Transform your PDFs into captivating audio with customizable voices or twin it with your own voice!

## Features

- **PDF to Speech**: Upload any PDF and convert its text to natural-sounding speech
- **Multiple Voices**: Choose from various English voices with different accents
- **Voice Cloning**: Clone the generated audio using your own voice sample
- **High Quality**: Uses advanced TTS models for natural speech synthesis

## How to Use

1. **Upload PDF**: Choose any PDF file you want to convert to audio
2. **Select Voice**: Pick from available voice styles (male/female, different accents)
3. **Generate Audio**: Click to process your PDF and generate speech
4. **Clone Voice (Optional)**: Upload a 15-second voice sample to clone the audio in your voice

## Technology Stack

- **Streamlit**: Web application framework
- **TTS (Coqui)**: Text-to-speech synthesis
- **PyPDF2**: PDF text extraction
- **Pydub**: Audio processing and merging

## Live Demo

[Access TalkTwin App](https://tts-s2s-clone-to-my-own-voice-talktwin-ecp7nrxl5ujczpgc69lfuu.streamlit.app/)

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Voice Sample Guidelines

For best voice cloning results:
- Use a clear, 15-second WAV file
- Speak naturally without background noise
- Include varied intonation and speech patterns
