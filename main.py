import os
import sys

# Auto-switch to the project's virtual environment if executed with global python
_script_dir = os.path.dirname(os.path.abspath(__file__))
_venv_python = os.path.join(_script_dir, "venv", "Scripts", "python.exe")
if os.path.exists(_venv_python):
    _curr_python = os.path.abspath(sys.executable).lower()
    _target_python = os.path.abspath(_venv_python).lower()
    if _curr_python != _target_python:
        import subprocess
        _res = subprocess.run([_venv_python] + sys.argv, cwd=_script_dir)
        sys.exit(_res.returncode)

# Ensure proper paths
sys.path.append(_script_dir)

from core.application import get_app
from core.background_worker import background_worker
from core.voice_worker import voice_worker
from core.system_monitor import system_monitor
from core.agent_orchestrator import AgentOrchestrator
from voice import manager as voice
import tools

orchestrator = AgentOrchestrator(verbose=False)

def print_banner():
    banner = r"""
========================================================================
   ___   _   ___ __   __ ___  ___ 
  |_  | /_\ | _ \\ \ / /|_ _|/ __|
 _/ /  / _ \|   / \ V /  | | \__ \
|___/ /_/ \_\_|_\  \_/  |___||___/   TERMINAL EDITION
========================================================================
    """
    print(banner)
    print(" [Core]     Bootstrapped & Ready")
    print(" [Model]    Groq / OpenAI-compatible LLM")
    print(" [Voice]    Whisper STT (GPU) + TTS Engine")
    print(" [Input]    Dual Mode: Type commands below OR speak into microphone")
    print("------------------------------------------------------------------------")
    print(" Special commands: 'help', 'voice on', 'voice off', 'status', 'exit'")
    print("========================================================================\n")

def run_face_id_check():
    print("[Security] Checking Biometric Security System...")
    has_profile = os.path.exists("master_face_sface.npy")
    has_models = os.path.exists("face_detection_yunet_2023mar.onnx") and os.path.exists("face_recognition_sface_2021dec.onnx")

    if not has_profile or not has_models:
        print("[Security] Face ID models or master profile not found. Continuing in Standard Mode.\n")
        return

    try:
        from security.face_id import verify_user_face
        print("[Security] Master Face ID profile detected.")
        choice = input(" -> Run Face ID camera verification now? [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            if verify_user_face():
                print("[Security] Identity verified successfully! Welcome back, Commander.\n")
            else:
                print("[Security] Face verification failed or timed out. Running in Standard Mode.\n")
        else:
            print("[Security] Skipped Face ID check. High-risk commands will prompt when executed.\n")
    except Exception as e:
        print(f"[Security] Camera/Face ID check skipped: {e}\n")

def handle_terminal_input():
    voice_active = voice_worker.running
    
    while True:
        try:
            prompt_symbol = "Jarvis [Voice ON] > " if voice_active else "Jarvis [Voice OFF] > "
            user_input = input(prompt_symbol).strip()
            
            if not user_input:
                continue
                
            cmd = user_input.lower()
            
            if cmd in ("exit", "quit", "q"):
                print("\n[Jarvis]: Shutting down systems. Goodbye!")
                voice.speak("Shutting down systems. Goodbye!")
                break
                
            elif cmd == "help":
                print("\n--- AVAILABLE CAPABILITIES & COMMANDS ---")
                print(" - Type any question or command naturally (e.g. 'What time is it?')")
                print(" - 'voice on' / 'voice off' : Enable/disable background microphone listening")
                print(" - 'status'                : View system metrics and background status")
                print(" - 'clear'                 : Clear the terminal screen")
                print(" - 'exit' / 'quit'         : Gracefully terminate Jarvis")
                print(" - Tools: OS tools, PowerShell execution, File read/create/delete,")
                print("          Permanent SQLite memory, Gemini Screen Analysis, Gmail/Calendar.\n")
                continue
                
            elif cmd == "voice on":
                if not voice_active:
                    voice_worker.start()
                    voice_active = True
                    print("[VoiceWorker] Continuous microphone listening enabled.\n")
                else:
                    print("[VoiceWorker] Voice listening is already active.\n")
                continue
                
            elif cmd == "voice off":
                if voice_active:
                    voice_worker.stop()
                    voice_active = False
                    print("[VoiceWorker] Microphone listening paused. (Terminal input only)\n")
                else:
                    print("[VoiceWorker] Voice listening is already off.\n")
                continue
                
            elif cmd == "clear":
                os.system("cls" if os.name == "nt" else "clear")
                print_banner()
                continue
                
            elif cmd == "status":
                from core.system_monitor import system_monitor
                print(f"[Status] Background Worker: {'Running' if background_worker.running else 'Stopped'}")
                print(f"[Status] Voice Worker:      {'Running' if voice_worker.running else 'Stopped'}")
                print(f"[Status] System Monitor:    {'Running' if system_monitor.running else 'Stopped'}\n")
                continue
                
            # Process command via Orchestrator
            print("\n[Thinking...]")
            response = orchestrator.process_request(user_input)
            
            clean_text = response.encode('ascii', 'ignore').decode() if response else "No response returned."
            print(f"\n[Jarvis]: {clean_text}\n")
            
            # Speak response aloud
            try:
                voice.speak(clean_text)
            except Exception:
                pass
                
        except (KeyboardInterrupt, EOFError):
            print("\n\n[System] Interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n[Error processing command]: {e}\n")

def main():
    # 1. Boot Core Application (Loads .env, Vault, DB, EventBus)
    get_app()
    print_banner()

    # 2. Biometric Face ID Check
    run_face_id_check()

    # 3. Start Background Workers
    print("[System] Starting background automation worker...")
    background_worker.start()

    print("[System] Starting background system monitor...")
    system_monitor.start()

    from core.feature_manager import feature_manager
    if feature_manager.is_feature_enabled("voice_input"):
        print("[System] Starting voice listener thread (Faster-Whisper on GPU)...")
        voice_worker.start()
    else:
        print("[System] Voice input disabled in config.json (Terminal mode only).")
    print("[System] All systems operational!\n")

    # 4. Run Interactive Terminal Loop
    try:
        handle_terminal_input()
    finally:
        print("[System] Stopping background workers...")
        background_worker.stop()
        voice_worker.stop()
        system_monitor.stop()
        print("[System] Shutdown complete. Have a great day!\n")

if __name__ == "__main__":
    main()
