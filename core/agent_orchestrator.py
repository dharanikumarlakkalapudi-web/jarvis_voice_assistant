import json
import sys
from agents.agent_manager import agent_manager
from tools.tool_registry import tool_registry
from security.security_manager import SecurityManager
from core.feature_manager import feature_manager

security_manager = SecurityManager()


class AgentOrchestrator:
    def __init__(self, verbose=True, max_history_messages=10, confirm_callback=None):
        self.verbose = verbose
        self.max_history_messages = max_history_messages
        self.confirm_callback = confirm_callback
        self.history = []

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def clear_history(self):
        self.history.clear()

    def _select_agent_id(self, user_input: str, requested_agent_id: str = "personal_agent") -> str:
        query_lower = user_input.lower()
        if "proactive_agent" in query_lower:
            return "proactive_agent"

        # Mixed-intent keywords that require GeneralAgent's wider toolset
        general_keywords = ("email", "mail", "gmail", "calendar", "schedule", "meeting", "remember", "memory", "volume", "brightness", "play", "youtube", "spotify", "search")
        has_general_intent = any(k in query_lower for k in general_keywords)

        if not has_general_intent:
            if any(k in query_lower for k in ("vision", "screenshot", "screen")) and feature_manager.is_feature_enabled("vision"):
                return "vision_agent"
            if any(k in query_lower for k in ("code", "script", "python")) and feature_manager.is_feature_enabled("coding_agent"):
                return "coding_agent"

        return requested_agent_id or "personal_agent"

    def _confirm_action(self, tool_name: str, tool_args_str: str, agent_id: str) -> bool:
        if self.confirm_callback is not None:
            return bool(self.confirm_callback(tool_name, tool_args_str))
        # Do not block headless/non-interactive runs or automated background tasks
        if agent_id == "proactive_agent" or not sys.stdin or not sys.stdin.isatty():
            return True
        try:
            ans = input(f"\n[Security] Confirm sensitive action '{tool_name}' ({tool_args_str})? [y/N]: ").strip().lower()
            return ans in ("y", "yes")
        except Exception:
            return False

    def process_request(self, user_input: str, agent_id: str = "personal_agent"):
        self._log("\n--- COMMAND LIFECYCLE STARTED ---")

        # 1. Agent Selection
        selected_id = self._select_agent_id(user_input, agent_id)
        agent = agent_manager.get_agent(selected_id) or agent_manager.get_agent("personal_agent")
        self._log(f"[Agent Selection] Using: {agent.agent_id}")

        # Publish event so listeners/UI can track active agent
        from core.event_bus import event_bus
        event_bus.publish("agent.changed", {"agent_id": agent.agent_id})

        # 2. Setup AI Provider
        from ai.provider_manager import provider_manager
        provider = provider_manager.get_default_provider()
        provider.model = provider_manager.get_default_model()

        # 3. Get Tool Schemas for this agent, filtered by FeatureManager flags
        enabled_tools = [t for t in agent.allowed_tools if feature_manager.is_tool_enabled(t)]
        schemas = tool_registry.get_all_schemas(allowed_tool_names=enabled_tools)

        # Include rolling history for interactive conversations (skip for background proactive checks)
        active_history = self.history[-self.max_history_messages:] if agent.agent_id != "proactive_agent" else None

        # 4. First AI Pass (Planning / Tool Selection)
        self._log(f"[Planning] Sending request to {provider.__class__.__name__}...")
        response = provider.generate_response(
            prompt=user_input,
            system_prompt=agent.system_instructions,
            tools=schemas,
            history=active_history
        )

        # 5. Check if tools were requested
        if not response.get("tool_calls"):
            self._log("[Execution] No tools requested. Direct response.")
            reply = response.get("text", "") or ""
            self._record_history(agent.agent_id, user_input, reply)
            return reply

        # 6. Tool Execution Loop
        tool_results_text = "Here are the results of the tool executions:\n"

        for tc in response["tool_calls"]:
            tool_name = tc["name"]
            tool_args_str = tc["arguments"]
            self._log(f"[Tool Selected] {tool_name}")

            tool = tool_registry.get_tool(tool_name)
            if not tool:
                tool_results_text += f"- {tool_name} failed: Tool not registered.\n"
                continue

            if not feature_manager.is_tool_enabled(tool_name):
                res = f"Execution blocked: Feature required for '{tool_name}' is disabled in config.json."
                security_manager.log_security_event(agent.agent_id, tool_name, "execute", tool.risk_level, "disabled", res)
                tool_results_text += f"- {tool_name} returned: {res}\n"
                continue

            # 7. Security Check
            decision = security_manager.evaluate_action(agent.agent_id, tool_name, tool.risk_level)
            self._log(f"[Security Check] Decision for {tool_name}: {decision}")

            if decision == "denied":
                res = "Execution blocked by Security Policy."
            elif decision == "face_id_required":
                self._log("[Security] Face ID verification required! Activating camera...")
                try:
                    from security.face_id import verify_user_face
                    authorized = verify_user_face()
                    if authorized:
                        self._log("[Security] Face verified. Proceeding with execution.")
                        kwargs = json.loads(tool_args_str) if tool_args_str else {}
                        res = tool.execute(**kwargs)
                    else:
                        res = "Execution blocked: Face ID verification failed."
                except Exception as e:
                    res = f"Execution blocked: Face verification error: {str(e)}"
            elif decision == "confirmation_required":
                if self._confirm_action(tool_name, tool_args_str, agent.agent_id):
                    try:
                        kwargs = json.loads(tool_args_str) if tool_args_str else {}
                        res = tool.execute(**kwargs)
                    except Exception as e:
                        res = f"Execution failed: {str(e)}"
                else:
                    res = "Execution cancelled by user confirmation prompt."
            else:
                try:
                    kwargs = json.loads(tool_args_str) if tool_args_str else {}
                    res = tool.execute(**kwargs)
                except Exception as e:
                    res = f"Execution failed: {str(e)}"

            security_manager.log_security_event(agent.agent_id, tool_name, "execute", tool.risk_level, decision, res)
            self._log(f"[Execution] Result: {res}")
            tool_results_text += f"- {tool_name} returned: {res}\n"

        # 8. Final AI Pass (Synthesize response)
        self._log("[Result Validation] Passing results back to AI for final synthesis...")
        final_prompt = (
            f"User Request: {user_input}\n\n"
            f"{tool_results_text}\n\n"
            "All requested tools have been executed. Provide the final natural language response summarizing the outcome for the user. Do not call any tools."
        )

        final_system = (
            f"{agent.system_instructions}\n"
            "NOTE: Tool executions are complete. You must reply strictly in plain conversational text."
        )

        try:
            final_response = provider.generate_response(
                prompt=final_prompt,
                system_prompt=final_system
            )
            response_text = final_response.get("text", "")
        except Exception as e:
            self._log(f"[Result Validation Fallback] {e}")
            response_text = tool_results_text.strip()

        if not response_text or not response_text.strip():
            response_text = tool_results_text.strip()

        self._record_history(agent.agent_id, user_input, response_text)
        self._log("--- COMMAND LIFECYCLE COMPLETED ---\n")
        return response_text

    def _record_history(self, agent_id: str, user_input: str, assistant_reply: str):
        if agent_id == "proactive_agent":
            return
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": assistant_reply})
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages:]
