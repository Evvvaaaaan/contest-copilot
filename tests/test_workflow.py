"""Run the actual HTTP controller with distinct, bounded CLI fixture processes."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow_test_server", ROOT / "web/server.py")
web = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(web)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        fixture = self.root / "workflow-codex"
        fixture.write_text(f"#!{sys.executable}\n" + (ROOT / "tests/fixtures/workflow_codex.py").read_text())
        fixture.chmod(0o700)
        self.app = web.App(self.root / "data", codex=str(fixture), turn_timeout=8)
        self.server = web.make_server(self.app, 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.token = self.request("/api/session")["token"]
        self.project = self.request("/api/projects", {"title": "Workflow fixture"}, expected=201)["id"]
        self.directory = self.app.directory(self.project)
        self.workspace = self.directory / "workspace"
        self.endpoint = f"/api/projects/{self.project}"
        self.contract = {"project": "Workflow fixture", "intent": "Verify a real local artifact",
                         "max_iterations": 4, "conditions": [{"id": "core", "source": "User agreement",
                         "required": True, "requirement": "Product file says good", "method": "Execute file check",
                         "target": "good", "applicability": "Fixture product"}]}
        self.limits = {"max_turns": 8, "max_seconds": 30, "stagnation_rounds": 2}

    def tearDown(self):
        if self.project in self.app.jobs:
            self.app.stop(self.project)
        deadline = time.monotonic() + 5
        while self.app.jobs and time.monotonic() < deadline:
            time.sleep(.03)
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def request(self, path, body=None, expected=200):
        request = Request(self.base + path, data=None if body is None else json.dumps(body).encode(),
                          headers={"X-Local-Token": getattr(self, "token", ""), "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                self.assertEqual(response.status, expected)
                return json.loads(response.read())
        except HTTPError as error:
            with error:
                raw = error.read().decode()
                self.assertEqual(error.code, expected, raw)
                return json.loads(raw)

    def write(self, name, value):
        (self.workspace / name).write_text(json.dumps(value))

    def start(self, mode="fail_first"):
        self.write("fixture-mode.json", {"mode": mode})
        self.write("workflow-proposal.json", {"contract": self.contract, "limits": self.limits})
        proposal = self.request(self.endpoint)["proposal"]
        self.request(self.endpoint + "/approve", {"hash": proposal["hash"]}, expected=202)
        return proposal

    def wait(self, seconds=10):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.project not in self.app.jobs:
                return self.request(self.endpoint)
            time.sleep(.03)
        self.fail("Workflow fixture exceeded bounded wait")

    def history(self):
        path = self.directory / "fixture-history.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_fail_fix_pass_uses_fresh_read_only_reviewer_contexts(self):
        self.start()
        result = self.wait()
        self.assertEqual(result["workflow"]["status"], "ready_for_user_review", result["workflow"])
        self.assertEqual(result["workflow"]["turns"], 4)
        self.assertEqual(result["progress"]["iteration"], 2)
        state = json.loads((self.workspace / "progress.json").read_text())
        self.assertEqual(state["iterations"][0]["results"]["core"]["verdict"], "fail")
        self.assertEqual(state["iterations"][1]["results"]["core"]["verdict"], "pass")
        history = self.history()
        self.assertEqual([entry["role"] for entry in history], ["developer", "reviewer"] * 2)
        self.assertEqual(len({entry["schema"] for entry in history}), 4)
        for entry in history:
            self.assertNotIn("resume", entry["argv"])
            if entry["role"] == "reviewer":
                self.assertIn('sandbox_mode="read-only"', entry["argv"])
                self.assertNotIn("User conversation:", entry["prompt"])
        self.assertTrue(result["records"]["decisions"])

    def test_changed_proposal_rejected_before_any_work(self):
        self.write("workflow-proposal.json", {"contract": self.contract, "limits": self.limits})
        proposal = self.request(self.endpoint)["proposal"]
        self.limits["max_turns"] = 6
        self.write("workflow-proposal.json", {"contract": self.contract, "limits": self.limits})
        self.request(self.endpoint + "/approve", {"hash": proposal["hash"]}, expected=400)
        self.assertFalse((self.workspace / "progress.json").exists())
        self.assertEqual(self.history(), [])

    def test_turn_limit_does_not_claim_success(self):
        self.limits["max_turns"] = 2
        self.start()
        result = self.wait()
        self.assertEqual(result["workflow"]["status"], "limit_reached")
        self.assertEqual(result["workflow"]["turns"], 2)
        self.assertEqual(result["progress"]["unmet_required"], ["core"])

    def test_stagnation_stops_before_exhausting_turns(self):
        self.limits["stagnation_rounds"] = 1
        self.start("always_fail")
        result = self.wait()
        self.assertEqual(result["workflow"]["status"], "stalled")
        self.assertEqual(result["workflow"]["turns"], 4)

    def test_elapsed_time_limit_stops_waiting_worker(self):
        self.limits["max_seconds"] = 1
        self.start("wait_first")
        result = self.wait(seconds=6)
        self.assertEqual(result["workflow"]["status"], "limit_reached")
        self.assertEqual(result["workflow"]["turns"], 1)
        self.assertNotEqual(result["progress"]["status"], "ready_for_user_review")

    def test_resume_rejects_outside_progress_edit(self):
        self.start("needs_user")
        result = self.wait()
        self.assertEqual(result["workflow"]["status"], "needs_user")
        path = self.workspace / "progress.json"
        state = json.loads(path.read_text())
        state["external_edit"] = True
        path.write_text(json.dumps(state))
        error = self.request(self.endpoint + "/resume", {}, expected=400)
        self.assertIn("변경", error["error"])
        self.assertEqual(len(self.history()), 1)

    def test_no_tool_evidence_cannot_pass(self):
        self.limits["max_turns"] = 2
        self.start("no_evidence")
        result = self.wait()
        self.assertEqual(result["progress"]["conditions"][0]["verdict"], "unverified")
        self.assertNotEqual(result["workflow"]["status"], "ready_for_user_review")

    def test_failed_command_only_evidence_cannot_pass(self):
        self.limits["max_turns"] = 2
        self.start("failed_evidence")
        result = self.wait()
        self.assertNotEqual(result["workflow"]["status"], "ready_for_user_review")
        self.assertEqual(result["progress"]["unmet_required"], ["core"])

    def test_unrelated_success_cannot_hide_failed_condition_check(self):
        self.limits["max_turns"] = 2
        self.start("unrelated_success")
        result = self.wait()
        self.assertEqual(result["progress"]["conditions"][0]["verdict"], "unverified")
        self.assertEqual(result["progress"]["unmet_required"], ["core"])
        self.assertNotEqual(result["workflow"]["status"], "ready_for_user_review")

    def test_missing_evidence_rejects_all_verdicts_before_mutation_and_can_resume(self):
        self.contract["conditions"].append(dict(self.contract["conditions"][0], id="second"))
        self.start("missing_evidence")
        failed = self.wait()
        self.assertEqual(failed["workflow"]["status"], "failed")
        state = json.loads((self.workspace / "progress.json").read_text())
        self.assertEqual(state["iterations"][0]["results"], {})
        self.request(self.endpoint + "/resume", {}, expected=202)
        resumed = self.wait()
        self.assertEqual(resumed["workflow"]["status"], "ready_for_user_review", resumed["workflow"])
        self.assertEqual(resumed["workflow"]["turns"], 3)
        self.assertEqual(resumed["progress"]["iteration"], 1)
        self.assertEqual([entry["role"] for entry in self.history()], ["developer", "reviewer", "reviewer"])

    def test_post_pass_feedback_requires_revision_before_finalization(self):
        self.start("pass")
        passed = self.wait()
        self.assertEqual(passed["workflow"]["status"], "ready_for_user_review")
        self.write("submission-spec.json", {"title": "Pending output settings"})
        self.request(self.endpoint + "/message", {"text": "같은 목표를 유지하면서 설명을 개선해 주세요."}, expected=202)
        feedback = self.wait()
        self.assertEqual(feedback["workflow"]["status"], "needs_user")
        self.assertTrue(feedback["workflow"]["revision_requested"])
        self.assertEqual(feedback["workflow"]["limits"], passed["workflow"]["limits"])
        self.assertEqual(feedback["workflow"]["turns"], 2)
        self.assertNotEqual(feedback["progress"]["status"], "ready_for_user_review")
        error = self.request(self.endpoint + "/finalize", {"hash": feedback["submission_spec"]["hash"]}, expected=400)
        self.assertIn("의견", error["error"])
        self.request(self.endpoint + "/resume", {}, expected=202)
        revised = self.wait()
        self.assertEqual(revised["workflow"]["status"], "ready_for_user_review")
        self.assertEqual(revised["workflow"]["turns"], 4)
        self.assertEqual(revised["progress"]["iteration"], 2)
        self.assertNotEqual(revised["progress"]["artifact_version"], passed["progress"]["artifact_version"])
        self.assertFalse(revised["workflow"]["revision_requested"])

    def test_developer_cannot_modify_progress(self):
        self.start("tamper_progress")
        result = self.wait()
        self.assertEqual(result["workflow"]["status"], "failed")
        self.assertIn("검증 상태", result["workflow"]["reason"])
        self.assertEqual(len(self.history()), 1)

    def test_reviewer_cannot_change_frozen_artifact(self):
        self.start("tamper_artifact")
        result = self.wait()
        self.assertEqual(result["workflow"]["status"], "failed")
        self.assertIn("결과물", result["workflow"]["reason"])

    def test_stop_resume_preserves_cumulative_budget(self):
        self.start("wait_first")
        deadline = time.monotonic() + 4
        while not (self.directory / "fixture-waiting").exists() and time.monotonic() < deadline:
            time.sleep(.03)
        self.assertTrue((self.directory / "fixture-waiting").exists())
        self.request(self.endpoint + "/stop", {})
        stopped = self.wait()
        self.assertEqual(stopped["workflow"]["status"], "interrupted")
        self.assertEqual(stopped["workflow"]["turns"], 1)
        self.request(self.endpoint + "/resume", {}, expected=202)
        resumed = self.wait()
        self.assertEqual(resumed["workflow"]["status"], "ready_for_user_review")
        self.assertEqual(resumed["workflow"]["turns"], 3)
        self.assertGreaterEqual(resumed["workflow"]["elapsed_seconds"], stopped["workflow"]["elapsed_seconds"])

    def test_simulation_two_rounds_with_distinct_participant_contexts(self):
        participants = [{"id": name, "role": "user", "goals": ["Save time"], "constraints": [],
                         "knowledge": ["Private-" + name], "resources": {}, "basis": ["Synthetic test fixture"]}
                        for name in ("alice", "bob")]
        self.write("simulation-plan.json", {"candidate_id": "candidate", "candidate_version": "v1",
                   "question": "What changes?", "max_rounds": 2, "baseline": {}, "participants": participants})
        plan = self.request(self.endpoint)["simulation_plan"]
        self.request(self.endpoint + "/simulate", {"hash": plan["hash"]}, expected=202)
        result = self.wait()
        summary = result["simulations"][0]
        self.assertEqual(summary["status"], "completed", result)
        self.assertEqual(summary["completed_rounds"], 2)
        self.assertEqual(summary["current_adopters"], 2)
        self.assertEqual(summary["exposed_participants"], 2)
        history = self.history()
        self.assertEqual(len(history), 4)
        for entry in history:
            self.assertEqual(entry["role"], "participant")
            self.assertFalse("Private-alice" in entry["prompt"] and "Private-bob" in entry["prompt"])

    def test_finalize_accepts_current_version_and_builds_actual_files(self):
        self.start("pass")
        result = self.wait()
        self.assertEqual(result["progress"]["status"], "ready_for_user_review")
        from project_records import Records
        source = Records(self.workspace).add_source({"title": "Fixture official notice", "url": "https://example.org/notice",
                 "status": "inspected", "locator": "Output rule", "accessed_at": "2026-10-12", "excerpt": "Produce a report"})
        self.write("submission-spec.json", {"project": "Workflow fixture", "title": "Checked report",
                   "official_instructions": [{"id": "format", "text": "Produce a report", "source_id": source["id"], "condition_ids": ["core"]}],
                   "accepted": {}, "sections": [{"title": "Result", "claims": [{"kind": "planned", "text": "Fixture result", "source_ids": [source["id"]]}]}],
                   "formats": [{"format": "md", "filename": "report.md"}, {"format": "html", "filename": "report.html"}]})
        spec = self.request(self.endpoint)["submission_spec"]
        manifest = self.request(self.endpoint + "/finalize", {"hash": spec["hash"]})
        self.assertFalse(manifest["externally_submitted"])
        self.assertEqual(manifest["accepted"]["artifact_version"], result["progress"]["artifact_version"])
        self.assertIn("Checked report", (self.workspace / "submission/report.html").read_text())
        self.assertTrue((self.workspace / "submission/report.md").is_file())


if __name__ == "__main__":
    unittest.main()
