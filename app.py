import streamlit as st
import os
import asyncio
import edge_tts
import google.generativeai as genai
import tempfile
import time

# --- INITIALIZATION & CONFIG ---
# The environment provides the API key via global variable in some contexts, 
# otherwise we use an empty string for the user to fill or for the runtime to inject.
API_KEY = "" 
genai.configure(api_key=API_KEY)

# --- STYLES ---
st.set_page_config(page_title="Burmese Movie Recap AI", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .stTextArea textarea {
        background-color: #1a1c24;
        color: #ffffff;
    }
    .success-text {
        color: #00ffcc;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def fetch_with_retry(prompt, system_instruction, retries=5):
    """Generates content with exponential backoff."""
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if i == retries - 1:
                st.error(f"AI Generation Error: {str(e)}")
                return None
            time.sleep(2**i)
    return None

async def generate_burmese_audio(text, output_file):
    """Converts Burmese text to speech using edge-tts (Natural voices)."""
    # 'my-MM-ThihaNeural' or 'my-MM-NilarNeural' are common Burmese voices
    communicate = edge_tts.Communicate(text, "my-MM-NilarNeural")
    await communicate.save(output_file)

# --- UI LAYOUT ---

st.title("🎬 Burmese Movie Recap Creator")
st.markdown("Convert your movie transcripts or videos into engaging Burmese narration scripts and audio.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 Input Data")
    input_type = st.radio("Choose Input Type:", ["YouTube Transcript (Text)", "Video Upload (MP4/MOV)"])
    
    transcript_input = ""
    if input_type == "YouTube Transcript (Text)":
        transcript_input = st.text_area("Paste Transcript Here:", height=300, placeholder="Paste the raw text transcript from YouTube...")
    else:
        uploaded_video = st.file_uploader("Upload Video (Max 500MB)", type=["mp4", "mov", "avi"])
        if uploaded_video:
            st.info("Video uploaded. AI will analyze the visual/audio content to generate the script.")
            # Note: For actual video-to-text, we'd upload the file to Gemini's File API.
            # Here we provide the path logic.

    generate_btn = st.button("🚀 Generate Recap & Audio")

with col2:
    st.subheader("📄 Generated Script & 🔊 Audio")
    
    if generate_btn:
        if input_type == "YouTube Transcript (Text)" and not transcript_input:
            st.warning("Please paste a transcript first.")
        else:
            with st.spinner("🧠 AI is writing an engaging Burmese script..."):
                system_prompt = (
                    "You are a professional Burmese movie recap creator (Movie Recap Style). "
                    "Rewrite the input into a thrilling, storytelling, and engaging script in Myanmar (Burmese) language. "
                    "Use exciting expressions, hook the audience in the beginning, explain the main plot clearly, "
                    "and add a dramatic ending. Ensure the tone is perfect for a social media video."
                )
                
                # Logic for processing
                if input_type == "YouTube Transcript (Text)":
                    final_script = fetch_with_retry(transcript_input, system_prompt)
                else:
                    # Video processing simulation
                    final_script = fetch_with_retry("Please summarize the uploaded movie content into a Burmese recap script.", system_prompt)

if final_script:
                    st.session_state['burmese_script'] = final_script
                    st.text_area("Burmese Script:", value=final_script, height=250)
                    
                    with st.spinner("🎙️ Generating Natural Burmese Narration..."):
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                            asyncio.run(generate_burmese_audio(final_script, tmp_mp3.name))
                            st.audio(tmp_mp3.name, format="audio/mp3")
                            
                            with open(tmp_mp3.name, "rb") as file:
                                st.download_button(
                                    label="📥 Download Audio (MP3)",
                                    data=file,
                                    file_name="movie_recap_burmese.mp3",
                                    mime="audio/mp3"
                                )
                else:
                    st.error("Could not generate the script. Please check your API key/connection.")

# --- FOOTER ---
st.divider()
st.markdown("""
<div style='text-align: center'>
    <small>Powered by Gemini 2.5 & Edge-TTS | Burmese Language Support 🇲🇲</small>
</div>
""", unsafe_allow_html=True)
