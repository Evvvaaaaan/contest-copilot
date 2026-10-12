"""Protocol test double only. Never used by the shipped web application."""

import json
from pathlib import Path
import signal
import subprocess
import sys
import time


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


if "login" in sys.argv:
    print("Test fixture authenticated")
    sys.exit(0)

prompt = sys.stdin.read()
emit({"type": "thread.started", "thread_id": "test-thread"})
if "TEST_ORPHAN" in prompt:
    subprocess.Popen([sys.executable, "-c", "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(20)"])
    sys.exit(0)
if "TEST_FAIL" in prompt:
    emit({"type": "turn.failed", "error": {"message": "Intentional fixture failure"}})
    sys.exit(1)
if "TEST_WAIT" in prompt:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(0.1)
Path("ui-state.json").write_text(json.dumps({"phase": "research", "summary": "Fixture progress",
                                           "next_action": "Fixture next step"}))
emit({"type": "item.completed", "item": {"id": "item_0", "type": "agent_message",
      "text": "Fixture resumed response" if "resume" in sys.argv else "Fixture first response"}})
emit({"type": "turn.completed"})
