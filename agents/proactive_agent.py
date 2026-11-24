from .base_agent import BaseAgent

class ProactiveAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "proactive_agent"

    @property
    def display_name(self) -> str:
        return "Background Monitor"

    @property
    def allowed_tools(self) -> list:
        return [
            "read_email",
            "read_calendar"
        ]

    @property
    def system_instructions(self) -> str:
        return """
You are JARVIS's Proactive Background Agent.
You run silently in a separate thread.
Your job is to check the user's unread emails and upcoming calendar events according to the automation prompt.
If you find something highly urgent or a briefing is requested, synthesize a concise summary.
If checking for urgent alerts and nothing is urgent, output exactly 'NO_ALERT'.
"""
