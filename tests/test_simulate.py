"""Exercise isolated observations, bounded rounds, durable actions and CLI resume."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "contest-copilot/scripts/simulate.py"
SPEC = importlib.util.spec_from_file_location("simulate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = MODULE.Simulation(self.root)
        self.config = {"candidate_id": "alpha", "candidate_version": "v1", "question": "What impedes uptake?",
                       "max_rounds": 2, "baseline": {"scenario": "A hypothetical local tool"},
                       "action_costs": {"try": {"time": 2}, "adopt": {"budget": 3}},
                       "participants": [{"id": name, "role": "user", "goals": ["Save time"],
                            "constraints": ["Limited budget"], "knowledge": [f"Private-{name}"],
                            "resources": {"time": 2, "budget": 3}, "basis": ["Explicit synthetic fixture"]}
                           for name in ("alice", "bob", "carol")]}
        self.run = self.engine.create(self.config)["run_id"]

    def action(self, actor="alice", kind="try", event="event-1", **extra):
        return {"event_id": event, "actor_id": actor, "type": kind, "reason": "Scenario decision", **extra}

    def apply(self, **kwargs):
        return self.engine.apply(self.run, self.action(**kwargs))

    def test_rounds_resume_resource_costs_and_unique_denominator(self):
        self.apply()
        self.apply(actor="bob", kind="reject", event="event-2")
        self.apply(actor="carol", kind="wait", event="event-3")
        self.engine.advance(self.run)
        resumed = MODULE.Simulation(self.root)
        resumed.apply(self.run, self.action(kind="adopt", event="event-4"))
        resumed.apply(self.run, self.action(actor="bob", kind="wait", event="event-5"))
        resumed.apply(self.run, self.action(actor="carol", kind="wait", event="event-6"))
        complete = resumed.advance(self.run)
        self.assertEqual(complete["state"]["status"], "completed")
        self.assertEqual(complete["state"]["participants"]["alice"]["resources"], {"time": 0, "budget": 0})
        summary = resumed.summary(self.run)
        self.assertEqual(summary["current_adopters"], 1)
        self.assertEqual(summary["exposed_participants"], 2)
        self.assertEqual(summary["synthetic_adoption_fraction"], .5)
        self.assertEqual(summary["completed_rounds"], 2)
        self.assertEqual(summary["candidate_version"], "v1")
        with self.assertRaisesRegex(ValueError, "not running"):
            resumed.advance(self.run)

    def test_invalid_actions_never_modify_disk(self):
        path = self.root / "simulations" / self.run / "run.json"
        before = path.read_bytes()
        bad = [self.action(kind="adopt"), self.action(actor="missing"),
               self.action(kind="share", target_id="alice", content="Private"),
               self.action(kind="ask", target_id="missing", content="Question"),
               self.action(resources={"budget": 999}), self.action(event="../escape")]
        for action in bad:
            with self.assertRaises(ValueError):
                self.engine.apply(self.run, action)
            self.assertEqual(before, path.read_bytes())
        with self.assertRaisesRegex(ValueError, "Every participant"):
            self.engine.advance(self.run)
        self.assertEqual(before, path.read_bytes())

    def test_insufficient_resources_and_allowed_options(self):
        config = deepcopy(self.config)
        config["participants"][0]["resources"]["time"] = 1
        run = self.engine.create(config)["run_id"]
        types = [x["type"] for x in self.engine.observation(run, "alice")["allowed_actions"]]
        self.assertNotIn("try", types)
        self.assertNotIn("adopt", types)
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            self.engine.apply(run, self.action())

    def test_private_messages_and_profiles(self):
        self.apply(kind="share", target_id="bob", content="Only Bob sees this")
        alice = self.engine.observation(self.run, "alice")
        bob = self.engine.observation(self.run, "bob")
        carol = self.engine.observation(self.run, "carol")
        self.assertIn("Only Bob sees this", json.dumps(bob))
        self.assertNotIn("Only Bob sees this", json.dumps(carol))
        self.assertNotIn("Private-alice", json.dumps(bob))
        self.assertNotIn("Private-bob", json.dumps(alice))
        self.assertNotIn("reason", bob["state"]["memory"][0])
        self.assertEqual(alice["allowed_actions"], [])
        self.assertEqual(self.engine.summary(self.run)["exposed_ids"], ["alice", "bob"])

    def test_duplicate_retry_and_concurrency_are_idempotent(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: MODULE.Simulation(self.root).apply(self.run, self.action()), range(4)))
        self.assertTrue(all(len(result["events"]) == 1 for result in results))
        run = self.engine.read(self.run)
        self.assertEqual(run["state"]["participants"]["alice"]["resources"]["time"], 0)
        with self.assertRaisesRegex(ValueError, "different action"):
            self.apply(kind="wait")
        with self.assertRaisesRegex(ValueError, "already acted"):
            self.apply(kind="wait", event="second")

    def test_candidates_reset_and_hashes_explain_differences(self):
        self.apply()
        other_config = deepcopy(self.config)
        other_config.update(candidate_id="beta", candidate_version="v2")
        other_config["action_costs"]["try"]["time"] = 1
        other = self.engine.create(other_config)
        first = self.engine.read(self.run)
        self.assertEqual(first["baseline_hash"], other["baseline_hash"])
        self.assertNotEqual(first["config_hash"], other["config_hash"])
        self.assertEqual(other["events"], [])
        self.assertEqual(other["state"]["participants"]["alice"]["memory"], [])
        self.assertEqual(other["state"]["participants"]["alice"]["resources"]["time"], 2)
        other_config["baseline"]["scenario"] = "Different conditions"
        self.assertNotEqual(first["baseline_hash"], self.engine.create(other_config)["baseline_hash"])

    def test_stop_is_partial_and_idempotent(self):
        self.apply(kind="wait")
        first = self.engine.stop(self.run)
        self.assertEqual(first, self.engine.stop(self.run))
        summary = self.engine.summary(self.run)
        self.assertEqual(summary["status"], "stopped")
        self.assertEqual(summary["completed_rounds"], 0)
        self.assertIsNone(summary["synthetic_adoption_fraction"])
        with self.assertRaisesRegex(ValueError, "not running"):
            self.apply(actor="bob", event="later")
        self.assertEqual(first, self.apply(kind="wait"))

    def test_ids_symlinks_and_config_are_rejected(self):
        for run in ("../other", "/tmp/other", "x/y", ""):
            with self.assertRaises(ValueError):
                self.engine.read(run)
        (self.root / "simulations" / "linked").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.engine.read("linked")
        for invalid in (True, 0, -1, 1.5):
            config = deepcopy(self.config)
            config["max_rounds"] = invalid
            with self.assertRaises(ValueError):
                self.engine.create(config)
        config = deepcopy(self.config)
        config["participants"][0]["resources"]["time"] = float("nan")
        with self.assertRaises(ValueError):
            self.engine.create(config)

    def test_cli_create_observe_act_resume_and_summary(self):
        config = self.root / "config.json"
        config.write_text(json.dumps(self.config), encoding="utf-8")
        def cli(*args, ok=True):
            result = subprocess.run([sys.executable, str(SCRIPT), "--workspace", str(self.root), *args],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
            return json.loads(result.stdout if ok else result.stderr)
        run = cli("create", "--config", str(config))["run_id"]
        self.assertEqual(cli("observe", "--run", run, "--actor", "bob")["profile"]["id"], "bob")
        action = self.root / "action.json"
        action.write_text(json.dumps(self.action()), encoding="utf-8")
        cli("act", "--run", run, "--input", str(action))
        self.assertEqual(cli("status", "--run", run)["state"]["acted"], ["alice"])
        self.assertEqual(cli("summary", "--run", run)["action_counts"], {"try": 1})
        self.assertIn("Every participant", cli("advance", "--run", run, ok=False)["error"])
        self.assertEqual(cli("stop", "--run", run)["state"]["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
