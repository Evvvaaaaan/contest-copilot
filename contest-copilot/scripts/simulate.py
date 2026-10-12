#!/usr/bin/env python3
"""Persist bounded stakeholder experiments; the host LLM supplies actions.

Config: candidate_id, candidate_version, question, max_rounds, baseline (public
scenario object), participants [{id, role, goals, constraints, knowledge,
resources, basis}]. Text collections are lists of strings; resources are a map
of nonnegative numbers. Optional action_costs maps action names to resource
cost maps. All participants are scheduled once per round, sequentially.

Action: {event_id, actor_id, type, reason}; ask/share also require target_id and
content. try marks a trial (not a real product test), adopt requires a trial,
reject changes the current decision, wait does nothing. Costs apply to every
accepted action; ask/share messages are private to sender and receiver.

Each run.json atomically contains config, state and events under a process lock.
baseline_hash excludes candidate identity, question and action costs; those
differences remain in config and config_hash and must be reviewed in comparisons.
No API, model inference, real-user measurement or forecast accuracy is implied.
"""

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid


ACTIONS = ("try", "adopt", "reject", "ask", "share", "wait")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")


def require(value, message):
    if not value:
        raise ValueError(message)


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value), "Invalid identifier.")
    return value


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def resource_map(value):
    require(isinstance(value, dict), "Resources and costs must be objects.")
    for name, amount in value.items():
        require(nonempty(name), "Resource names must be nonempty strings.")
        require(type(amount) in (int, float) and math.isfinite(amount) and amount >= 0,
                "Resources and costs must be finite nonnegative numbers.")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def validate_config(config):
    require(isinstance(config, dict), "Config must be an object.")
    identifier(config.get("candidate_id"))
    for field in ("candidate_version", "question"):
        require(nonempty(config.get(field)), f"Missing {field}.")
    require(type(config.get("max_rounds")) is int and config["max_rounds"] > 0,
            "max_rounds must be a positive integer.")
    require(isinstance(config.get("baseline"), dict), "baseline must be a public scenario object.")
    participants = config.get("participants")
    require(isinstance(participants, list) and participants, "Participants must be a nonempty list.")
    ids = set()
    for person in participants:
        require(isinstance(person, dict), "Each participant must be an object.")
        pid = identifier(person.get("id"))
        require(pid not in ids, "Participant IDs must be unique.")
        ids.add(pid)
        require(nonempty(person.get("role")), "Each participant needs a role.")
        for field in ("goals", "constraints", "knowledge", "basis"):
            require(isinstance(person.get(field), list) and all(nonempty(x) for x in person[field]),
                    f"Participant {field} must be a list of nonempty strings.")
        resource_map(person.get("resources"))
    costs = config.get("action_costs", {})
    require(isinstance(costs, dict), "action_costs must be an object.")
    for action, resources in costs.items():
        require(action in ACTIONS, "Unknown action cost.")
        resource_map(resources)
    canonical(config)


class Simulation:
    def __init__(self, workspace):
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.root = self.workspace / "simulations"
        require(not self.root.is_symlink(), "Simulation storage cannot be a symlink.")
        self.root.mkdir(exist_ok=True)

    @contextmanager
    def _lock(self):
        require(not self.root.is_symlink(), "Simulation storage cannot be a symlink.")
        path = self.root / ".lock"
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags, 0o600), "a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _path(self, run_id):
        identifier(run_id)
        directory = self.root / run_id
        path = directory / "run.json"
        require(not directory.is_symlink() and not path.is_symlink(), "Run paths cannot be symlinks.")
        return path

    def _load(self, run_id):
        path = self._path(run_id)
        require(path.is_file(), "Run does not exist.")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, run):
        path = self._path(run["run_id"])
        descriptor, temporary = tempfile.mkstemp(prefix=".run-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(canonical(run) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def create(self, config):
        validate_config(config)
        config = deepcopy(config)
        config.setdefault("action_costs", {})
        baseline = {key: config[key] for key in ("participants", "max_rounds", "baseline")}
        baseline["rules"] = "sequential-one-action-per-participant-v1"
        run_id = "run-" + uuid.uuid4().hex
        run = {"schema_version": 1, "run_id": run_id, "created_at": now(),
               "config": config, "config_hash": digest(config), "baseline_hash": digest(baseline),
               "state": {"status": "running", "round": 1, "completed_rounds": 0,
                         "acted": [], "stop_reason": None,
                         "participants": {person["id"]: {"resources": deepcopy(person["resources"]),
                             "tried": False, "decision": "undecided", "exposed": False,
                             "memory": []} for person in config["participants"]}}, "events": []}
        with self._lock():
            self._path(run_id).parent.mkdir()
            self._save(run)
        return run

    def read(self, run_id):
        with self._lock():
            return self._load(run_id)

    def observation(self, run_id, actor_id):
        identifier(actor_id)
        run = self.read(run_id)
        require(actor_id in run["state"]["participants"], "Unknown participant.")
        profile = next(p for p in run["config"]["participants"] if p["id"] == actor_id)
        own = run["state"]["participants"][actor_id]
        options = []
        if run["state"]["status"] == "running" and actor_id not in run["state"]["acted"]:
            for action in ACTIONS:
                if action == "try" and own["tried"]:
                    continue
                if action == "adopt" and (not own["tried"] or own["decision"] == "adopted"):
                    continue
                if action == "reject" and own["decision"] == "rejected":
                    continue
                if action in ("ask", "share") and len(run["config"]["participants"]) == 1:
                    continue
                costs = run["config"]["action_costs"].get(action, {})
                if all(own["resources"].get(name, 0) >= amount for name, amount in costs.items()):
                    options.append({"type": action, "costs": costs,
                                    "requires_target_and_content": action in ("ask", "share")})
        return {"run_id": run_id, "candidate_id": run["config"]["candidate_id"],
                "candidate_version": run["config"]["candidate_version"],
                "round": run["state"]["round"], "status": run["state"]["status"],
                "baseline": run["config"]["baseline"], "profile": profile, "state": own,
                "roster": [{"id": p["id"], "role": p["role"]} for p in run["config"]["participants"]],
                "allowed_actions": options,
                "disclaimer": "Synthetic scenario. Other actors' private contexts are omitted."}

    def apply(self, run_id, action):
        require(isinstance(action, dict), "Action must be an object.")
        identifier(action.get("event_id"))
        identifier(action.get("actor_id"))
        kind = action.get("type")
        require(kind in ACTIONS, "Unknown action type.")
        require(nonempty(action.get("reason")), "A concise reason is required.")
        allowed = {"event_id", "actor_id", "type", "reason"}
        if kind in ("ask", "share"):
            allowed.update(("target_id", "content"))
            identifier(action.get("target_id"))
            require(nonempty(action.get("content")), "Message content is required.")
        require(set(action) == allowed, "Unexpected or missing action fields.")
        canonical(action)
        with self._lock():
            run = self._load(run_id)
            previous = next((e for e in run["events"] if e.get("event_id") == action["event_id"]), None)
            if previous:
                require(previous["action"] == action, "event_id already belongs to a different action.")
                return run
            state = run["state"]
            require(state["status"] == "running", "Run is not running.")
            actor_id = action["actor_id"]
            require(actor_id in state["participants"], "Unknown participant.")
            require(actor_id not in state["acted"], "Participant has already acted this round.")
            actor = state["participants"][actor_id]
            if kind == "try":
                require(not actor["tried"], "Participant has already tried the candidate.")
            if kind == "adopt":
                require(actor["tried"], "Adoption requires a prior trial.")
                require(actor["decision"] != "adopted", "Participant has already adopted.")
            if kind == "reject":
                require(actor["decision"] != "rejected", "Participant has already rejected.")
            if kind in ("ask", "share"):
                require(action["target_id"] in state["participants"] and action["target_id"] != actor_id,
                        "Target must be another participant.")
            costs = run["config"]["action_costs"].get(kind, {})
            require(all(actor["resources"].get(name, 0) >= amount for name, amount in costs.items()),
                    "Insufficient resources.")
            before = {"resources": deepcopy(actor["resources"]), "tried": actor["tried"],
                      "decision": actor["decision"]}
            for name, amount in costs.items():
                actor["resources"][name] = actor["resources"].get(name, 0) - amount
            if kind == "try":
                actor["tried"] = True
            elif kind in ("adopt", "reject"):
                actor["decision"] = "adopted" if kind == "adopt" else "rejected"
            if kind != "wait":
                actor["exposed"] = True
            memory = {"event_id": action["event_id"], "round": state["round"], "action": deepcopy(action)}
            actor["memory"].append(memory)
            if kind in ("ask", "share"):
                receiver = state["participants"][action["target_id"]]
                receiver["memory"].append({"event_id": action["event_id"], "round": state["round"],
                                           "from": actor_id, "type": kind, "content": action["content"]})
                receiver["exposed"] = True
            state["acted"].append(actor_id)
            run["events"].append({"event_id": action["event_id"], "type": "action", "at": now(),
                                  "round": state["round"], "action": deepcopy(action),
                                  "before": before, "after": {"resources": deepcopy(actor["resources"]),
                                      "tried": actor["tried"], "decision": actor["decision"]}})
            self._save(run)
            return run

    def advance(self, run_id):
        with self._lock():
            run = self._load(run_id)
            state = run["state"]
            require(state["status"] == "running", "Run is not running.")
            require(set(state["acted"]) == set(state["participants"]),
                    "Every participant must act or wait before advancing.")
            state["completed_rounds"] = state["round"]
            run["events"].append({"type": "round_completed", "round": state["round"], "at": now()})
            if state["round"] >= run["config"]["max_rounds"]:
                state["status"] = "completed"
                state["stop_reason"] = "round_limit"
            else:
                state["round"] += 1
                state["acted"] = []
            self._save(run)
            return run

    def stop(self, run_id):
        with self._lock():
            run = self._load(run_id)
            if run["state"]["status"] == "running":
                run["state"]["status"] = "stopped"
                run["state"]["stop_reason"] = "requested"
                run["events"].append({"type": "stopped", "round": run["state"]["round"], "at": now()})
                self._save(run)
            return run

    def summary(self, run_id):
        run = self.read(run_id)
        events = [e for e in run["events"] if e["type"] == "action"]
        exposed = set()
        decisions = {}
        for event in events:
            action = event["action"]
            if action["type"] != "wait":
                exposed.add(action["actor_id"])
            if "target_id" in action:
                exposed.add(action["target_id"])
            if action["type"] in ("adopt", "reject"):
                decisions[action["actor_id"]] = action["type"]
        adopted = sum(value == "adopt" for value in decisions.values())
        return {"run_id": run_id, "candidate_id": run["config"]["candidate_id"],
                "candidate_version": run["config"]["candidate_version"],
                "config_hash": run["config_hash"], "baseline_hash": run["baseline_hash"],
                "question": run["config"]["question"], "status": run["state"]["status"],
                "stop_reason": run["state"]["stop_reason"],
                "completed_rounds": run["state"]["completed_rounds"],
                "participants": len(run["config"]["participants"]), "exposed_participants": len(exposed),
                "exposed_ids": sorted(exposed), "action_counts": dict(Counter(e["action"]["type"] for e in events)),
                "current_adopters": adopted, "current_rejecters": sum(v == "reject" for v in decisions.values()),
                "synthetic_adoption_fraction": adopted / len(exposed) if exposed else None,
                "exposure_definition": "Unique actors of non-wait actions or recipients of ask/share messages.",
                "event_ids": [e["event_id"] for e in events],
                "limitations": ["Synthetic behavior is not real adoption or verified product performance.",
                                "No sampling uncertainty or model sensitivity has been measured.",
                                "A completed run means its round budget ended, not that the idea passed."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("create").add_argument("--config", required=True, help="JSON file path")
    for name in ("observe", "act", "advance", "status", "summary", "stop"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True)
        if name == "observe":
            command.add_argument("--actor", required=True)
        if name == "act":
            command.add_argument("--input", required=True, help="JSON action file path")
    args = parser.parse_args()
    try:
        engine = Simulation(args.workspace)
        if args.command == "create":
            result = engine.create(json.loads(Path(args.config).read_text(encoding="utf-8")))
        elif args.command == "observe":
            result = engine.observation(args.run, args.actor)
        elif args.command == "act":
            result = engine.apply(args.run, json.loads(Path(args.input).read_text(encoding="utf-8")))
        else:
            result = getattr(engine, "read" if args.command == "status" else args.command)(args.run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
