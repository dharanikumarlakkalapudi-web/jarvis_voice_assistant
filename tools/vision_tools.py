import os
import io
import time
from PIL import ImageGrab
from .base_tool import BaseTool
from security.security_manager import SecurityManager

class TakeScreenshotTool(BaseTool):
    @property
    def name(self) -> str:
        return "take_screenshot"

    @property
    def description(self) -> str:
        return "Takes a screenshot of the main display and saves it to a file."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string", 
                    "description": r"Optional custom filepath. If not provided, saves to e:\jarvis\screenshot.png"
                }
            }
        }

    @property
    def risk_level(self) -> int:
        return SecurityManager.RISK_LOW

    def execute(self, filepath: str = None, **kwargs) -> str:
        if not filepath:
            filepath = r"e:\jarvis\screenshot.png"
        try:
            # Add a tiny delay to ensure menus close if triggered by hotkey
            time.sleep(0.5)
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            return f"Screenshot saved successfully to {filepath}."
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"

class AnalyzeScreenTool(BaseTool):
    @property
    def name(self) -> str:
        return "analyze_screen"

    @property
    def description(self) -> str:
        return "Takes a screenshot and analyzes its contents using a Vision model. Use this to 'see' what is on the screen."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "What to look for or analyze on the screen."},
                "screen": {
                    "type": "string",
                    "description": "Which monitor to inspect ('all', 'left', 'right', '1', '2'). Defaults to 'all'."
                }
            },
            "required": ["prompt"]
        }

    @property
    def risk_level(self) -> int:
        return SecurityManager.RISK_LOW

    def execute(self, prompt: str, screen: str = "all", **kwargs) -> str:
        from vision.screen import analyze_screen
        return analyze_screen(prompt=prompt, screen=screen)
