#!/usr/bin/env python3
"""Persist competition acceptance checks and resume points (Python 3.9+, macOS/Linux).

Run --help for commands. This tool records supplied judgments; it does not run
tests, authenticate user approval, or independently interpret evidence.
"""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_contract(contract):
    require(isinstance(contract, dict), "Contract must be an object.")
    for key in ("project", "intent"):
        require(nonempty(contract.get(key)), f"Missing contract field: {key}")
    limit = contract.get("max_iterations")
    require(type(limit) is int and limit > 0, "max_iterations must be a positive integer.")
    conditions = contract.get("conditions")
    require(isinstance(conditions, list) and conditions, "Conditions must be a nonempty list.")
    ids = set()
    for item in conditions:
        require(isinstance(item, dict), "Each condition must be an object.")
        for key in ("id", "source", "requirement", "method", "target", "applicability"):
            require(nonempty(item.get(key)), f"Missing condition field: {key}")
        require(type(item.get("required")) is bool, "required must be a boolean.")
        require(item["id"] not in ids, "Condition IDs must be unique.")
        ids.add(item["id"])
    require(any(item["required"] for item in conditions), "At least one required condition is needed.")
    return contract


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def capture(paths, root, state_path):
    result = []
    for raw in paths:
        path = Path(raw)
        path = (root / path).resolve() if not path.is_absolute() else path.resolve()
        require(path != state_path, "The mutable state file cannot be evidence or an artifact.")
        require(path.is_file(), f"File does not exist: {path}")
        if not any(item["path"] == str(path) for item in result):
            result.append({"path": str(path), "sha256": fingerprint(path)})
    return result


def unchanged(files):
    try:
        return all(fingerprint(item["path"]) == item["sha256"] for item in files)
    except OSError:
        return False


def report(state):
    contract = state["contract"]
    current = state["iterations"][-1] if state["iterations"] else None
    current_contract = bool(current and current["contract_version"] == state["contract_version"])
    artifact_current = bool(current and unchanged(current["artifacts"]))
    results = []
    for item in contract["conditions"]:
        record = current["results"].get(item["id"]) if current else None
        reason = None
        if not record:
            reason = "no_result"
        elif not current_contract:
            reason = "contract_changed"
        elif not artifact_current:
            reason = "artifact_changed_or_missing"
        elif not unchanged(record["evidence"]):
            reason = "evidence_changed_or_missing"
        verdict = "unverified" if reason else record["verdict"]
        results.append({"id": item["id"], "required": item["required"],
                        "requirement": item["requirement"], "method": item["method"],
                        "target": item["target"], "source": item["source"],
                        "applicability": item["applicability"],
                        "verdict": verdict, "reason": reason,
                        "record": record})
    unmet = [item["id"] for item in results if item["required"] and item["verdict"] != "pass"]
    used = len(state["iterations"])
    status = "ready_for_user_review" if not unmet else (
        "limit_reached" if used >= contract["max_iterations"] else "in_progress")
    return {"project": contract["project"], "intent": contract["intent"],
            "status": status, "contract_version": state["contract_version"],
            "iteration": used, "remaining_iterations": max(0, contract["max_iterations"] - used),
            "artifact_version": current["artifact_version"] if current else None,
            "unmet_required": unmet, "conditions": results,
            "checkpoint": state["checkpoint"],
            "checkpoint_matches_current_iteration": bool(state["checkpoint"] and
                state["checkpoint"]["iteration"] == used and
                state["checkpoint"]["contract_version"] == state["contract_version"] and
                artifact_current)}


def save(path, state):
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".contest-state-", delete=False) as handle:
            name = handle.name
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def execute(args, path):
    now = datetime.now(timezone.utc).isoformat()
    if args.command == "init":
        require(not path.exists(), "State already exists; use status or contract.")
        root = Path(args.project_root).resolve()
        require(root.is_dir(), "Project root must exist.")
        state = {"schema_version": 1, "project_root": str(root),
                 "contract": validate_contract(read_json(args.contract)),
                 "contract_version": 1, "iterations": [], "checkpoint": None, "history": []}
        detail = {"contract": state["contract"], "decision": args.decision}
    else:
        state = read_json(path)
        require(state.get("schema_version") == 1, "Unsupported state schema.")
        root = Path(state["project_root"])
        if args.command == "status":
            return report(state)
        if args.command == "history":
            return state["history"]
        detail = {}
        if args.command == "contract":
            state["contract"] = validate_contract(read_json(args.contract))
            state["contract_version"] += 1
            detail = {"contract": state["contract"], "decision": args.decision}
        elif args.command == "start":
            require(len(state["iterations"]) < state["contract"]["max_iterations"],
                    "Iteration limit reached; report incomplete or record an agreed contract revision.")
            current = {"number": len(state["iterations"]) + 1,
                       "contract_version": state["contract_version"],
                       "artifact_version": args.version,
                       "artifacts": capture(args.artifact, root, path),
                       "results": {}, "started_at": now}
            state["iterations"].append(current)
            detail = current.copy()
        elif args.command == "record":
            require(bool(state["iterations"]), "Start an iteration before recording results.")
            current = state["iterations"][-1]
            require(current["contract_version"] == state["contract_version"],
                    "Contract changed; start a new iteration.")
            require(unchanged(current["artifacts"]), "Artifacts changed; start a new iteration.")
            condition = next((item for item in state["contract"]["conditions"]
                              if item["id"] == args.condition), None)
            require(condition is not None, "Unknown condition ID.")
            if args.verdict == "pass":
                require(bool(args.evidence), "A pass requires evidence files.")
            if args.verdict == "waived":
                require(not condition["required"], "Required conditions cannot be waived.")
                require(nonempty(args.decision), "A waiver requires a user decision reference.")
            detail = {"condition": args.condition, "verdict": args.verdict,
                      "evidence": capture(args.evidence, root, path), "note": args.note,
                      "method": args.method, "review_mode": args.review_mode,
                      "decision": args.decision, "recorded_at": now}
            current["results"][args.condition] = detail
        elif args.command == "checkpoint":
            detail = {"phase": args.phase, "next_action": args.next_action,
                      "note": args.note, "preview_url": args.preview_url,
                      "iteration": len(state["iterations"]),
                      "contract_version": state["contract_version"], "saved_at": now}
            state["checkpoint"] = detail
    state["history"].append({"event": args.command, "at": now,
                             "iteration": len(state["iterations"]),
                             "contract_version": state["contract_version"], "detail": detail})
    save(path, state)
    return report(state)


def text_arg(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("Value must not be blank.")
    return value


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--state", required=True, help="Project-specific JSON state file.")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("init", "contract"):
        command = commands.add_parser(name, help="Record an agreed acceptance contract.")
        command.add_argument("--contract", required=True, help="JSON contract file.")
        command.add_argument("--decision", required=True, type=text_arg,
                             help="Reference to the user's actual agreement; not an approval request.")
        if name == "init":
            command.add_argument("--project-root", required=True)
    command = commands.add_parser("start", help="Start a review iteration on a frozen artifact snapshot.")
    command.add_argument("--version", required=True, type=text_arg)
    command.add_argument("--artifact", action="append", required=True, help="File; repeat for all relevant files.")
    command = commands.add_parser("record", help="Record a reviewer verdict and existing evidence.")
    command.add_argument("--condition", required=True, type=text_arg)
    command.add_argument("--verdict", required=True, choices=("pass", "fail", "unverified", "waived"))
    command.add_argument("--method", required=True, type=text_arg, help="Actual check command or inspection method.")
    command.add_argument("--note", required=True, type=text_arg, help="Observed result, limitations, or blocker.")
    command.add_argument("--review-mode", required=True, choices=("separate_context", "shared_context"))
    command.add_argument("--evidence", action="append", default=[])
    command.add_argument("--decision", type=text_arg)
    command = commands.add_parser("checkpoint", help="Save progress and the next executable action.")
    command.add_argument("--phase", required=True, choices=("research", "idea_assessment", "planning",
                         "simulation", "development", "validation", "user_feedback", "finalization"))
    command.add_argument("--next-action", required=True, type=text_arg)
    command.add_argument("--note", required=True, type=text_arg)
    command.add_argument("--preview-url", type=text_arg)
    commands.add_parser("status", help="Recheck stored file hashes and report current acceptance status.")
    commands.add_parser("history", help="Show recorded events, previous contracts, and verdicts.")
    return result


def main():
    args = parser().parse_args()
    path = Path(args.state).resolve()
    try:
        if args.command == "init":
            path.parent.mkdir(parents=True, exist_ok=True)
        # Serialize cooperating CLI writers and readers; keep the lock file for safe reuse.
        with Path(str(path) + ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            output = execute(args, path)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
