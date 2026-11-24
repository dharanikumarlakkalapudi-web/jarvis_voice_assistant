import sys
import os

# Inject CUDA 12 DLLs into PATH for faster-whisper/ctranslate2
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_bin_cublas = os.path.join(current_dir, "..", r"venv\Lib\site-packages\nvidia\cublas\bin")
venv_bin_cudnn = os.path.join(current_dir, "..", r"venv\Lib\site-packages\nvidia\cudnn\bin")

if os.path.exists(venv_bin_cublas):
    os.environ["PATH"] = venv_bin_cublas + ";" + os.environ["PATH"]
if os.path.exists(venv_bin_cudnn):
    os.environ["PATH"] = venv_bin_cudnn + ";" + os.environ["PATH"]

# Set up global hotkey listener for Ctrl+Space
ctrl_space_pressed = False
def on_ctrl_space():
    global ctrl_space_pressed
    ctrl_space_pressed = True

def consume_hotkey():
    global ctrl_space_pressed
    if ctrl_space_pressed:
        ctrl_space_pressed = False
        return True
    return False

def on_ctrl_esc():
    import os
    print("\n[System] Ctrl+Esc pressed. Force quitting...")
    os._exit(0)

try:
    import keyboard
    from configuration.manager import config_manager as _cfg
    _hotkey = _cfg.get("activation.hotkey", "ctrl+space")
    keyboard_available = True
    keyboard.add_hotkey(_hotkey, on_ctrl_space)
    keyboard.add_hotkey('ctrl+esc', on_ctrl_esc)
except Exception:
    keyboard = None
    keyboard_available = False

from faster_whisper import WhisperModel
import warnings
import asyncio
import edge_tts
import pygame
import sounddevice as sd
import numpy as np
import time
import shutil

# Monkey-patch os.symlink to avoid Windows Admin privileges error (WinError 1314)
def dummy_symlink(src, dst, target_is_directory=False):
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except FileExistsError:
        pass
os.symlink = dummy_symlink

import torch
import torchaudio
import random
try:
    from speechbrain.inference.speaker import SpeakerRecognition
except ImportError:
    pass

voice_verifier = None
master_embedding = None
require_strict_verification = True
def init_voice_verification():
    global voice_verifier, master_embedding
    if os.path.exists("master_voice_print.pt"):
        if voice_verifier is None:
            print("\n[Loading Voice Biometrics Engine...]")
            # Force CPU to avoid CUDA deadlocks with faster-whisper
            voice_verifier = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb", 
                savedir="tmp_model", 
                run_opts={"device": "cpu"}
            )
            master_embedding = torch.load("master_voice_print.pt", map_location=torch.device('cpu'))

# Suppress some noisy warnings from faster-whisper/CTranslate2
warnings.filterwarnings("ignore")

import threading
import tempfile

_speak_lock = threading.Lock()

# ==========================================
# 1. TEXT-TO-SPEECH (TTS) SETUP
# ==========================================

def speak(text: str):
    """Speaks the given text using Edge TTS (thread-safe) and allows interruption."""
    from configuration.manager import config_manager
    if not config_manager.get("features.voice_output", True):
        return

    with _speak_lock:
        print(f"\n[Jarvis Speaking]: {text}")
        print("[Press 'Esc' to interrupt]")

        temp_file = None
        try:
            fd, temp_file = tempfile.mkstemp(prefix="jarvis_tts_", suffix=".mp3")
            os.close(fd)

            async def generate_audio():
                # Using a sophisticated British male voice (en-GB-RyanNeural) and slightly reduced speed for a composed delivery
                communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-5%")
                await communicate.save(temp_file)

            asyncio.run(generate_audio())

            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if keyboard_available and keyboard and keyboard.is_pressed('esc'):
                    pygame.mixer.music.stop()
                    print("\n[Interrupted]")
                    break
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
            pygame.mixer.quit()

        except Exception as e:
            print(f"[Edge TTS unavailable ({e}), using Windows Speech Engine fallback...]")
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
            except Exception as fallback_err:
                print(f"[TTS Fallback Error]: {fallback_err}")
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass


# ==========================================
# 2. SPEECH-TO-TEXT (STT) SETUP (Local Free)
# ==========================================
from configuration.manager import config_manager
model_size = config_manager.get("voice.model_size", "small")
# Prefer GPU (CUDA float16) for low-latency transcription, with automatic CPU (int8) fallback
try:
    whisper_model = WhisperModel(model_size, device="cuda", compute_type="float16")
except Exception as _cuda_err:
    print(f"[Voice] CUDA unavailable ({_cuda_err}); falling back to CPU (int8) for Faster-Whisper.")
    whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")

_cached_threshold = None

def calibrate_microphone(duration=0.5):
    """Calibrates baseline ambient noise once."""
    global _cached_threshold
    SAMPLE_RATE = 16000
    try:
        noise = sd.rec(int(SAMPLE_RATE * duration), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()
        baseline_energy = float(np.mean(np.abs(noise)))
        _cached_threshold = max(baseline_energy * 2.0, 0.003)
    except Exception:
        _cached_threshold = 0.005

def capture_speech_audio():
    """Listens to the microphone continuously and captures speech, preserving leading syllables."""
    global _cached_threshold
    SAMPLE_RATE = 16000
    CHUNK_DURATION = 0.05
    CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
    SILENCE_DURATION = 1.3
    
    if _cached_threshold is None:
        calibrate_microphone(0.4)
        
    energy_threshold = _cached_threshold
    
    import collections
    # 1.25 seconds of pre-roll to ensure initial words like 'Hey Jarvis' are never chopped off
    pre_roll_buffer = collections.deque(maxlen=25)
    audio_buffer = []
    is_speaking = False
    silence_time = 0.0
    wait_time = 0.0
    
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
            while True:
                chunk, overflow = stream.read(CHUNK_SIZE)
                energy = float(np.mean(np.abs(chunk)))
                
                # Detect speech vs silence
                if energy > energy_threshold:
                    if not is_speaking:
                        # Append the pre-roll first to capture the very beginning of speech
                        for pre_chunk in pre_roll_buffer:
                            audio_buffer.append(pre_chunk)
                    is_speaking = True
                    silence_time = 0.0
                else:
                    if is_speaking:
                        silence_time += CHUNK_DURATION
                    else:
                        wait_time += CHUNK_DURATION
                        # Continuously adapt threshold to ambient sound when silent
                        if len(pre_roll_buffer) == pre_roll_buffer.maxlen:
                            ambient = float(np.mean([np.mean(np.abs(p)) for p in pre_roll_buffer]))
                            if ambient > 0.001:
                                energy_threshold = max(ambient * 2.0, 0.003)
                                
                # If completely silent for 10 seconds, yield control back to the loop
                if not is_speaking and wait_time > 10.0:
                    return None
                    
                if is_speaking:
                    audio_buffer.append(chunk.flatten())
                else:
                    pre_roll_buffer.append(chunk.flatten())
                    
                # Stop listening if they pause after speaking
                if is_speaking and silence_time > SILENCE_DURATION:
                    break
                    
        if audio_buffer:
            return np.concatenate(audio_buffer)
    except Exception as e:
        print(f"[Microphone Error]: {e}")
        return None
    return None

def verify_speaker(audio_data) -> bool:
    """Verifies captured audio against master_voice_print.pt when voice biometrics is enabled."""
    init_voice_verification()
    if voice_verifier is None or master_embedding is None:
        return True
    try:
        threshold = float(os.getenv("VOICE_SIMILARITY_THRESHOLD", "0.5"))
        signal = torch.tensor(audio_data, dtype=torch.float32).unsqueeze(0)
        live_embedding = voice_verifier.encode_batch(signal)
        score = float(torch.nn.functional.cosine_similarity(
            master_embedding.flatten().unsqueeze(0),
            live_embedding.flatten().unsqueeze(0)
        ).item())
        if score >= threshold:
            return True
        print(f"[Voice Biometrics] Speaker rejected (score={score:.3f} < {threshold})")
        return False
    except Exception as e:
        print(f"[Voice Biometrics Warning]: {e}")
        return True


def listen() -> str:
    """Listens to the microphone continuously and transcribes live with Whisper."""
    audio_data = capture_speech_audio()
    if audio_data is None or len(audio_data) == 0:
        return ""

    if config_manager.get("voice.require_voice_verification", False):
        if not verify_speaker(audio_data):
            return ""
        
    # Normalize audio volume so Whisper receives strong, clear signal
    max_val = np.max(np.abs(audio_data))
    if max_val > 0.001:
        audio_data = (audio_data / max_val) * 0.90

    final_text = ""
    try:
        segments, info = whisper_model.transcribe(
            audio_data, 
            beam_size=5, 
            language="en",
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
            initial_prompt="Jarvis, Dharani, Hey Jarvis, hello, what is this room, tell me, open Chrome, Blender, code, time."
        )
        text = "".join([segment.text for segment in segments]).strip()
        
        # --- Common Phonetic & Accents Correction ---
        corrections = {
            "here are u": "how are u",
            "here are you": "how are you",
            "read me large emails": "read me last emails",
            "he was at this room": "what is this room",
            "he was": "hey jarvis",
            "hey travis": "hey jarvis",
            "service": "jarvis"
        }
        import re
        for wrong, right in corrections.items():
            text = re.sub(rf'\b{re.escape(wrong)}\b', right, text, flags=re.IGNORECASE)
            
        print(f"[Heard]: {text}")
        final_text = text
        
    except Exception as e:
        print(f"Transcription Error: {e}")
        final_text = ""
        
    return final_text
