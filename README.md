# Jarvis: Personal Voice Assistant (Terminal Edition)

> A voice and terminal AI assistant that controls your Windows PC, sees your screen, and verifies your face before risky actions.

## 🏗️ How It Works

```text
Microphone / Terminal
        │
        ▼
  Faster-Whisper (Local GPU STT, CPU int8 fallback)
        │
        ▼
  Agent Orchestrator & Router (General · Coding · Vision · Proactive)
        │
        ▼
  Security Policy (Risk Tiers · Face ID · Confirmations) ──▶ Tools & OS Control
        │
        ▼
  Edge TTS (Interruptible Speech Output) + Terminal Output
```

1. **Input:** Commands arrive either from the interactive terminal prompt or continuously from your microphone via `sounddevice` and local **Faster-Whisper**.
2. **Routing:** `AgentOrchestrator` maintains rolling conversation history and routes requests to specialized agents (`personal_agent`, `coding_agent`, `vision_agent`, `proactive_agent`), filtering tools through feature flags in `config.json`.
3. **Execution & Guardrails:** Every tool call is checked against `SecurityManager` risk levels and audited in SQLite (`jarvis_v2.db`) before running OS, filesystem, vision, web search, or calendar tools.
4. **Output:** The LLM synthesizes a natural-language reply, prints it to the console, and speaks it via thread-safe **Microsoft Edge TTS** (interruptible anytime with `Esc`).

## 🚀 Features

- **Dual-Mode Terminal & Voice Interface**: Type commands directly in the terminal or speak naturally via microphone.
- **Face ID & Biometric Security**: Uses YuNet + SFace face verification for high-risk actions and interactive confirmation prompts for sensitive actions.
- **Multi-Agent AI & Multi-Turn Memory**: Specialized agents for general tasks, coding, vision, and background automations powered by Groq / OpenAI and Gemini Vision, with rolling conversation history.
- **Speech-to-Text & Text-to-Speech**: Local Faster-Whisper on GPU (with automatic CPU `int8` fallback) and Microsoft Edge TTS playback (with Windows SAPI offline fallback).
- **Screen Capture & Vision Analysis**: Capture screenshots and analyze your screen in real time using Gemini Vision.
- **Web Search & Media Playback**: Live web search via DuckDuckGo (with Wikipedia fallback) and YouTube / Spotify playback.
- **Permanent SQLite Memory**: Long-term memory storage and retrieval backed by SQLite (`jarvis_v2.db`).
- **Core OS & System Controls**: System time, app launching, speaker volume & screen brightness control, PowerShell execution, and file read/create/delete.
- **Google Calendar & Cron Automations**: Fetch or schedule Google Calendar events (optional OAuth setup) and run background tasks on 5-field cron schedules.

## 🔒 Security Notes

Tools are classified into tiered risk levels enforced by `SecurityManager` and logged to `activity_logs` in SQLite:

- **Level 0–1 (Safe / Low Risk):** Time, memory, web search, screenshots, reading files, opening apps, volume/brightness — execute automatically.
- **Level 2 (Sensitive):** Actions like creating calendar events prompt for explicit interactive terminal confirmation (`[y/N]`) before running.
- **Level 3 (Dangerous):** **PowerShell execution** (`execute_powershell`) and **permanent file deletion** (`delete_file`) trigger live **Face ID verification** (YuNet + SFace cosine similarity) before execution. If verification fails, the action is blocked and logged.
- **Known Biometric Limitation (Spoofing):** SFace performs 2D facial embedding matching and does **not** perform liveness or anti-spoofing detection (e.g., blink, 3D depth, or IR checks). A high-resolution photo or video held up to the webcam could potentially fool it. Face ID here is intended as a convenient local friction gate against accidental or casual misuse—not hardened physical security.
- **Secrets Hygiene:** API keys are loaded from `.env` (or Windows Credential Manager via `keyring`) and excluded via `.gitignore`. Never commit `.env`, `credentials.json`, or `token.json`.

## ⚠️ Limitations

- **Windows Only:** Relies on Windows-specific APIs (`pycaw`, `win32com`, `winsound`, PowerShell, `os.startfile`). macOS and Linux are not supported.
- **GPU Recommended for Fast STT:** Faster-Whisper defaults to CUDA `float16` (`large-v3-turbo` in `config.json`). If CUDA is unavailable, it automatically falls back to **CPU (`int8`)**, which works but is noticeably slower on large models—switch `voice.model_size` to `"small"` or `"base.en"` in `config.json` for responsive CPU transcription.
- **TTS Network Dependency:** Primary voice output uses Microsoft Edge TTS (requires internet); offline fallback uses Windows SAPI voices.
- **Face ID Liveness:** No anti-spoofing / liveness check (see Security Notes above).
- **Terminal-Only UI:** Runs as a console application; there is no desktop GUI/HUD in this edition.

## 🛠️ Prerequisites

- **Windows 10/11** with **Python 3.10+** (Tested on Python 3.13)
- **NVIDIA GPU with CUDA** (recommended for fast Whisper STT; CPU `int8` fallback included)
- *(Optional)* Face ID ONNX models (download links below)

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dharanikumarlakkalapudi-web/jarvis_voice_assistant.git
   cd jarvis_voice_assistant
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

4. *(Optional)* **Download Face ID ONNX Models & Enroll Your Face:**
   Download the two OpenCV Zoo models into the project root directory (`jarvis_voice_assistant/`):
   - **YuNet Face Detector:** [`face_detection_yunet_2023mar.onnx`](https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx)
   - **SFace Face Recognizer:** [`face_recognition_sface_2021dec.onnx`](https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx)

   Or download both via PowerShell:
   ```powershell
   Invoke-WebRequest -Uri "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx" -OutFile "face_detection_yunet_2023mar.onnx"
   Invoke-WebRequest -Uri "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx" -OutFile "face_recognition_sface_2021dec.onnx"
   ```

   Then enroll your face profile (`master_face_sface.npy`):
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

---

License: [MIT](LICENSE)
