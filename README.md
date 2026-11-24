# Jarvis: Personal Voice Assistant (Terminal Edition)

Jarvis is a modular personal voice assistant for Windows built with Python. It integrates LLMs via Groq / OpenAI, Google Gemini Vision for screen analysis, computer vision for Face ID authentication, local Faster-Whisper GPU speech recognition, and proactive background automations—all accessible through an interactive terminal console and hands-free microphone input.

## 🚀 Features

- **Dual-Mode Terminal & Voice Interface**: Type commands directly in the terminal or speak naturally via microphone.
- **Face ID & Biometric Security**: Uses YuNet + SFace face verification for high-risk actions (PowerShell execution, file deletion) and interactive confirmation prompts for sensitive actions.
- **Multi-Agent AI & Multi-Turn Memory**: Specialized agents for general tasks, coding, vision, and background automations powered by Groq / OpenAI and Gemini Vision, with rolling conversation history.
- **Speech-to-Text & Text-to-Speech**: Local Faster-Whisper running on GPU for low-latency transcription with thread-safe Microsoft Edge TTS playback (interruptible with `Esc`).
- **Screen Capture & Vision Analysis**: Capture screenshots and analyze your screen in real time using Gemini Vision.
- **Web Search & Media Playback**: Live web search via DuckDuckGo (with Wikipedia fallback) and YouTube / Spotify playback.
- **Permanent SQLite Memory**: Long-term memory storage and retrieval backed by SQLite (`jarvis_v2.db`).
- **Core OS & System Controls**: System time, app launching, speaker volume & screen brightness control, PowerShell execution, and file read/create/delete.
- **Google Calendar & Cron Automations**: Fetch or schedule Google Calendar events (optional OAuth setup) and run background tasks on 5-field cron schedules.

## 🛠️ Prerequisites

- **Windows 10/11** with **Python 3.10+** (Tested on Python 3.13)
- **NVIDIA GPU with CUDA** (for GPU-accelerated Faster-Whisper STT)
- *(Optional)* Face ID ONNX models (`face_detection_yunet_2023mar.onnx` and `face_recognition_sface_2021dec.onnx`) if enabling Face ID

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dharanikumarlakkalapudi-web/persnal_voice_assistant.git
   cd persnal_voice_assistant
   ```

2. **Setup Virtual Environment & Install Dependencies:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```env
   GROQ_API_KEY="your-groq-key"
   MODEL_NAME="openai/gpt-oss-20b"
   VISION_OPENAI_API_KEY="your-google-ai-studio-gemini-key"
   VISION_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
   VISION_MODEL_NAME="gemini-flash-latest"
   ```

4. *(Optional)* **Enroll Face ID:**
   ```powershell
   python enroll_face.py
   ```

## 🚀 Usage

Start Jarvis from the project root (automatically activates the local `venv`):
```powershell
python main.py
```

Type commands at the `Jarvis >` prompt or speak into your microphone. Built-in terminal commands:
- `help` — Show available capabilities and commands
- `voice on` / `voice off` — Enable or pause microphone listening
- `status` — View background worker and monitor status
- `clear` — Clear the terminal screen
- `exit` / `quit` — Shut down Jarvis

See [JARVIS_CAPABILITIES.md](JARVIS_CAPABILITIES.md) for a detailed capability guide.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
