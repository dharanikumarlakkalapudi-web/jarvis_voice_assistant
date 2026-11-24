import threading
import time
from datetime import datetime
from core.event_bus import event_bus
from core.agent_orchestrator import AgentOrchestrator
from voice import manager as voice

class VoiceWorker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.orchestrator = AgentOrchestrator(verbose=True)
        self.is_sleeping = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        event_bus.publish("voice_worker.started", {})
        print("[VoiceWorker] Started continuous listening.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        event_bus.publish("voice_worker.stopped", {})
        print("[VoiceWorker] Stopped.")

    def _loop(self):
        time.sleep(1)
        event_bus.publish("voice.state", {"state": "SPEAKING"})
        msg = "Jarvis is online and ready. How can I help you?"
        event_bus.publish("voice.response", {"text": msg})
        voice.speak(msg)
        
        while self.running:
            try:
                if self.is_sleeping:
                    # Don't use microphone, just poll for hotkey to save CPU/privacy
                    time.sleep(0.1)
                    if voice.consume_hotkey():
                        self.is_sleeping = False
                        event_bus.publish("voice.state", {"state": "SPEAKING"})
                        voice.speak("I am awake. How can I help?")
                        event_bus.publish("voice.state", {"state": "IDLE"})
                    continue

                # 1. Listen for user input
                import winsound
                # Give a short beep before listening
                winsound.Beep(750, 150)
                
                event_bus.publish("voice.state", {"state": "LISTENING"})
                user_input = voice.listen()
                
                if not user_input or user_input.strip() == "":
                    event_bus.publish("voice.state", {"state": "IDLE"})
                    continue
                    
                print(f"[Voice Input]: {user_input}")
                
                # Check wake word requirement
                from configuration.manager import config_manager
                wake_words = config_manager.get("activation.wake_words", ["jarvis", "computer", "assistant"])
                require_wake_word = config_manager.get("activation.require_wake_word", False)
                hotkey_woke = voice.consume_hotkey()
                
                extended_wake_words = list(wake_words) + [
                    "hey jarvis", "hi jarvis", "ok jarvis", "okay jarvis",
                    "jarves", "travis", "harvest", "service"
                ]
                has_wake_word = any(ww.lower() in user_input.lower() for ww in extended_wake_words)
                
                if require_wake_word and not hotkey_woke and not has_wake_word:
                    print(f"(Debug: Ignoring input because no wake word was found)")
                    event_bus.publish("voice.state", {"state": "IDLE"})
                    continue
                
                # Clean leading wake word if present so the LLM gets the pure query
                import re
                clean_query = re.sub(r'^(hey\s+|hi\s+|ok\s+|okay\s+)?(jarvis|computer|assistant)[,\s]*', '', user_input, flags=re.I).strip()
                if clean_query:
                    user_input = clean_query
                
                event_bus.publish("voice.transcript", {"text": user_input})
                
                if any(word in user_input.lower() for word in ['exit', 'quit']):
                    event_bus.publish("voice.state", {"state": "SPEAKING"})
                    voice.speak("Shutting down voice systems.")
                    self.stop()
                    break
                    
                if 'sleep' in user_input.lower() or 'stop listening' in user_input.lower():
                    self.is_sleeping = True
                    event_bus.publish("voice.state", {"state": "SPEAKING"})
                    voice.speak("Going to sleep. Press control space for waking up.")
                    event_bus.publish("voice.state", {"state": "IDLE"})
                    continue
                    
                print(f"Jarvis is thinking...")
                event_bus.publish("voice.state", {"state": "PROCESSING"})
                
                # 2. Process through Orchestrator
                response_text = self.orchestrator.process_request(user_input)
                print(f"\n[Jarvis]: {response_text}\n")
                
                # Publish the AI's response to the transcript
                event_bus.publish("voice.response", {"text": response_text})
                
                # 3. Speak the response
                event_bus.publish("voice.state", {"state": "SPEAKING"})
                voice.speak(response_text)
                event_bus.publish("voice.state", {"state": "IDLE"})
                
            except Exception as e:
                print(f"[VoiceWorker Error]: {str(e)}")
                event_bus.publish("voice.state", {"state": "ERROR"})
                time.sleep(2)

voice_worker = VoiceWorker()
