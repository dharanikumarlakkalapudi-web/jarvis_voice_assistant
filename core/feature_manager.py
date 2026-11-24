from configuration.manager import config_manager


class FeatureManager:
    """Central registry that checks if features and their associated tools are enabled."""

    def __init__(self):
        # Maps feature IDs to their dotted config paths
        self.feature_map = {
            "voice_input": "features.voice_input",
            "voice_output": "features.voice_output",
            "screen_capture": "features.screen_capture",
            "vision": "features.vision",
            "gmail": "features.gmail",
            "calendar": "features.calendar",
            "coding_agent": "features.coding_agent",
            "web_search": "features.web_search",
            "os_control": "features.os_control",
            "terminal": "features.terminal",
        }

        # Maps tool names to the feature flag that governs them
        self.tool_feature_map = {
            "read_email": "gmail",
            "send_email": "gmail",
            "read_calendar": "calendar",
            "create_calendar_event": "calendar",
            "take_screenshot": "screen_capture",
            "analyze_screen": "vision",
            "web_search": "web_search",
            "execute_powershell": "os_control",
            "open_application": "os_control",
            "set_brightness": "os_control",
            "set_volume": "os_control",
        }

    def is_feature_enabled(self, feature_id: str) -> bool:
        if feature_id not in self.feature_map:
            return True

        config_path = self.feature_map[feature_id]
        return bool(config_manager.get(config_path, default=True))

    def is_tool_enabled(self, tool_name: str) -> bool:
        feature_id = self.tool_feature_map.get(tool_name)
        if not feature_id:
            return True
        return self.is_feature_enabled(feature_id)


feature_manager = FeatureManager()
