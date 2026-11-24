# Jarvis: Personal Voice Assistant (Terminal Edition)

Jarvis is a highly capable personal voice assistant built with Python. It integrates AI models via Groq / OpenAI, Google Gemini vision for screen analysis, computer vision for Face ID authentication, local Whisper voice recognition, and proactive agentic capabilities—all directly accessible from a sleek interactive terminal console.

## 🚀 Features

- **Dual-Mode Terminal & Voice Interface**: Type commands directly into the terminal or talk naturally using microphone speech recognition.
- **Face ID & Biometric Security**: Secure access using face detection (YuNet) and recognition (SFace) for high-risk commands, with interactive confirmation prompts for sensitive actions.
- **Multi-Modal AI & Multi-Turn Memory**: Specialized agents for vision, coding, and general tasks powered by Groq / OpenAI and Google Gemini Vision, with rolling conversation history.
- **Speech-to-Text & Text-to-Speech**: Faster-Whisper running locally on GPU for sub-second transcription with thread-safe Microsoft Edge TTS playback.
- **Screen Capture & Vision Analysis**: Take screenshots and analyze your display in real time using Gemini Vision.
- **Web Search & Media Playback**: Live web search via DuckDuckGo (with Wikipedia fallback) and YouTube / Spotify media playback.
- **Permanent SQLite Memory**: Long-term memory storage for user preferences and facts.
- **Core OS & System Controls**: System time, app launching, volume & screen brightness control, PowerShell execution, and file management.
- **Google Calendar & Cron Automations**: Fetch or schedule calendar events and run background tasks on 5-field cron schedules.
- **Blender 3D Modeling Ready**: Generate `bpy` scripts and control Blender procedurally or through real-time socket commands.

## 🛠️ Prerequisites

- **Python 3.9+** (Tested on Python 3.13)
- NVIDIA GPU with CUDA (optional, for accelerated Whisper STT)
- The necessary `.onnx` machine learning models for Face ID

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dharanikumarlakkalapudi-web/persnal_voice_assistant.git
   cd persnal_voice_assistant
   ```

2. **Setup Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Edit `.env` and set your API keys:
   ```env
   GROQ_API_KEY="your-groq-key"
   MODEL_NAME="openai/gpt-oss-20b"
   VISION_OPENAI_API_KEY="your-google-ai-studio-gemini-key"
   VISION_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
   VISION_MODEL_NAME="gemini-flash-latest"
   ```

## 🚀 Usage

Start Jarvis in the terminal:
```bash
python main.py
```
You can type commands directly in the `Jarvis > ` prompt or speak through your microphone! Type `help` for special commands or `exit` to quit.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
