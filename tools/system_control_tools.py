from .base_tool import BaseTool
from security.security_manager import SecurityManager

class SetBrightnessTool(BaseTool):
    @property
    def name(self) -> str:
        return "set_brightness"

    @property
    def description(self) -> str:
        return "Sets the system screen brightness to a specific percentage (0-100)."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "Brightness level from 0 to 100"}
            },
            "required": ["level"]
        }

    @property
    def risk_level(self) -> int:
        return SecurityManager.RISK_SAFE

    def execute(self, level: int, **kwargs) -> str:
        try:
            import screen_brightness_control as sbc
            clamped = max(0, min(100, int(level)))
            sbc.set_brightness(clamped)
            return f"Screen brightness set to {clamped}%."
        except Exception as e:
            return f"Failed to set brightness: {str(e)}"

class SetVolumeTool(BaseTool):
    @property
    def name(self) -> str:
        return "set_volume"

    @property
    def description(self) -> str:
        return "Sets the system volume to a specific percentage (0-100)."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "Volume level from 0 to 100"}
            },
            "required": ["level"]
        }

    @property
    def risk_level(self) -> int:
        return SecurityManager.RISK_SAFE

    def execute(self, level: int, **kwargs) -> str:
        try:
            from pycaw.pycaw import AudioUtilities

            devices = AudioUtilities.GetSpeakers()
            if hasattr(devices, "EndpointVolume"):
                volume = devices.EndpointVolume
            else:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import IAudioEndpointVolume
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))

            clamped = max(0, min(100, int(level)))
            scalar_level = clamped / 100.0
            volume.SetMasterVolumeLevelScalar(scalar_level, None)

            return f"System volume set to {clamped}%."
        except Exception as e:
            return f"Failed to set volume: {str(e)}"
