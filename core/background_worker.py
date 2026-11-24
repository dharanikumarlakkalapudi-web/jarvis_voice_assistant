import datetime
import json
import os
import threading
import time
from core.event_bus import event_bus
from core.agent_orchestrator import AgentOrchestrator


def _field_matches(field: str, value: int, is_weekday: bool = False) -> bool:
    """Matches a single 5-field cron token (supports *, */n, a-b, a-b/n, and comma lists)."""
    field = field.strip()
    if field == "*":
        return True

    for part in field.split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = max(1, int(step_str))
        else:
            base = part

        if base == "*":
            if value % step == 0:
                return True
        elif "-" in base:
            start_s, end_s = base.split("-", 1)
            start, end = int(start_s), int(end_s)
            if is_weekday:
                # Normalize Sunday=7 to 0
                vals = {v % 7 for v in range(start, end + 1, step)}
                if (value % 7) in vals:
                    return True
            else:
                if start <= value <= end and (value - start) % step == 0:
                    return True
        else:
            target = int(base)
            if is_weekday:
                if (value % 7) == (target % 7):
                    return True
            elif value == target:
                return True
    return False


def cron_matches(cron_expr: str, dt: datetime.datetime) -> bool:
    """Checks if a 5-field cron expression ('min hour dom month dow') matches dt."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False
    minute_f, hour_f, dom_f, month_f, dow_f = parts
    # Convert Python weekday (Mon=0..Sun=6) to standard cron weekday (Sun=0, Mon=1..Sat=6)
    cron_dow = (dt.weekday() + 1) % 7
    try:
        return (
            _field_matches(minute_f, dt.minute)
            and _field_matches(hour_f, dt.hour)
            and _field_matches(dom_f, dt.day)
            and _field_matches(month_f, dt.month)
            and _field_matches(dow_f, cron_dow, is_weekday=True)
        )
    except ValueError:
        return False


class BackgroundWorker:
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self.running = False
        self.thread = None
        self.orchestrator = AgentOrchestrator(verbose=False)
        self._last_run_minute = {}

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        event_bus.publish("background_worker.started", {"interval": self.interval})
        print(f"[BackgroundWorker] Started (checking schedules every {self.interval}s).")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        event_bus.publish("background_worker.stopped", {})
        print("[BackgroundWorker] Stopped.")

    def _should_run(self, auto: dict, now: datetime.datetime) -> bool:
        auto_id = auto.get("id", "unknown")
        minute_key = (now.year, now.month, now.day, now.hour, now.minute)
        if self._last_run_minute.get(auto_id) == minute_key:
            return False

        cron_expr = auto.get("cron")
        if cron_expr:
            return cron_matches(cron_expr, now)
        return True

    def _loop(self):
        while self.running:
            try:
                automations = []
                if os.path.exists("automations.json"):
                    with open("automations.json", "r", encoding="utf-8") as f:
                        automations = json.load(f)
                else:
                    automations = [{
                        "id": "urgent_email_check",
                        "cron": "*/15 * * * *",
                        "prompt": "Check unread emails. If there is anything highly urgent, summarize it as an alert. Otherwise, respond exactly with 'NO_ALERT'."
                    }]

                now = datetime.datetime.now()
                for auto in automations:
                    if not self.running:
                        break
                    if not self._should_run(auto, now):
                        continue

                    auto_id = auto.get("id", "unknown")
                    self._last_run_minute[auto_id] = (now.year, now.month, now.day, now.hour, now.minute)
                    print(f"\n[BackgroundWorker] Running scheduled automation: {auto_id}")
                    query = f"[HINT: Route to proactive_agent] {auto['prompt']}"

                    response = self.orchestrator.process_request(query)

                    if "NO_ALERT" not in response and response.strip() != "":
                        print(f"\n!!! [PROACTIVE ALERT: {auto_id}] !!!")
                        print(response)
                        event_bus.publish("proactive.alert", {"message": response, "id": auto_id})
                    else:
                        print(f"[BackgroundWorker] {auto_id} finished. Nothing urgent.")

            except Exception as e:
                print(f"[BackgroundWorker] Error during check: {e}")

            for _ in range(int(self.interval)):
                if not self.running:
                    break
                time.sleep(1)


background_worker = BackgroundWorker()
