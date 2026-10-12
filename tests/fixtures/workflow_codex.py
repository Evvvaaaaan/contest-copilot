"""Subprocess protocol fixture; never called by production application code."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import uuid


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


if "login" in sys.argv:
    print("Fixture authenticated")
    sys.exit(0)

prompt = sys.stdin.read()
if "--output-schema" not in sys.argv:
    emit({"type": "thread.started", "thread_id": "fixture-chat"})
    emit({"type": "item.completed", "item": {"id": "chat", "type": "agent_message", "text": "의견을 확인했습니다. 같은 조건으로 이어갈 수 있습니다."}})
    emit({"type": "turn.completed"})
    sys.exit(0)
schema_path = Path(sys.argv[sys.argv.index("--output-schema") + 1])
schema = json.loads(schema_path.read_text())
role = "developer" if "outcome" in schema["properties"] else "reviewer" if "verdicts" in schema["properties"] else "participant"
root = Path.cwd()
control = json.loads((root / "fixture-mode.json").read_text()) if (root / "fixture-mode.json").exists() else {}
mode = control.get("mode", "fail_first")
history_path = schema_path.parents[2] / "fixture-history.jsonl"
history = [json.loads(line) for line in history_path.read_text().splitlines()] if history_path.exists() else []
count = sum(item["role"] == role for item in history) + 1
with history_path.open("a") as stream:
    stream.write(json.dumps({"role": role, "argv": sys.argv, "schema": str(schema_path), "prompt": prompt}) + "\n")
emit({"type": "thread.started", "thread_id": "fixture-" + uuid.uuid4().hex})

if role == "developer":
    if mode == "wait_first" and count == 1:
        (root.parent / "fixture-waiting").write_text("ready")
        time.sleep(30)
    if mode == "tamper_progress":
        path = root / "progress.json"
        state = json.loads(path.read_text())
        state["unauthorized"] = True
        path.write_text(json.dumps(state))
    product = "bad" if mode in ("always_fail", "unrelated_success") or (mode == "fail_first" and count == 1) else "good"
    (root / "product.txt").write_text(product)
    result = {"outcome": "needs_user" if mode == "needs_user" and count == 1 else "ready_for_review",
              "summary": "검토할 결과물을 만들었습니다.", "question": "추가 결정을 알려 주세요." if mode == "needs_user" else "",
              "artifacts": ["product.txt"]}
elif role == "reviewer":
    if mode == "tamper_artifact":
        (root / "product.txt").write_text("changed during review")
    command = [sys.executable, "-c", "from pathlib import Path; import sys; value=Path('product.txt').read_text(); print(value); sys.exit(0 if value=='good' else 1)"]
    check = subprocess.run(command, capture_output=True, text=True)
    command_text = shlex.join(command)
    code = 1 if mode == "failed_evidence" else check.returncode
    if mode != "no_evidence":
        emit({"type": "item.completed", "item": {"id": "check", "type": "command_execution", "command": "/bin/zsh -lc " + shlex.quote(command_text),
              "aggregated_output": check.stdout, "exit_code": code, "status": "completed"}})
    if mode == "unrelated_success":
        unrelated = subprocess.run(["pwd"], capture_output=True, text=True)
        emit({"type": "item.completed", "item": {"id": "unrelated", "type": "command_execution", "command": "pwd",
              "aggregated_output": unrelated.stdout, "exit_code": unrelated.returncode, "status": "completed"}})
    contract = json.loads(prompt.split("Contract: ", 1)[1].splitlines()[0])
    result = {"summary": "실제 파일을 확인했습니다.", "verdicts": [{"condition_id": condition["id"],
              "verdict": "pass" if mode in ("no_evidence", "failed_evidence", "unrelated_success") or check.returncode == 0 else "fail",
              "method": "Execute product content check", "note": check.stdout.strip(),
              "evidence": ["missing-evidence.txt"] if mode == "missing_evidence" and count == 1 and index == 1 else [],
              "checks": [{"command": command_text, "expected_exit_code": 0}]} for index, condition in enumerate(contract["conditions"])]}
else:
    observation = json.loads(prompt[prompt.index("\n{") + 1:])
    kinds = [option["type"] for option in observation["allowed_actions"]]
    kind = "adopt" if "adopt" in kinds else "try" if "try" in kinds else "wait"
    result = {"type": kind, "reason": "주어진 가상 조건에 따른 판단입니다.", "target_id": "", "content": ""}

emit({"type": "item.completed", "item": {"id": "answer", "type": "agent_message", "text": json.dumps(result)}})
emit({"type": "turn.completed"})
