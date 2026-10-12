"""Exercise the real CLI against disposable project files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "contest-copilot/scripts/manage_state.py"


class StateFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "progress.json"
        self.artifact = self.root / "product.txt"
        self.artifact.write_text("version one", encoding="utf-8")
        self.evidence = self.root / "check.log"
        self.evidence.write_text("Observed output: expected value", encoding="utf-8")
        self.contract = {"project": "Example competition", "intent": "Preserve the user's purpose",
                         "max_iterations": 2, "conditions": [
            {"id": "core", "source": "User agreement", "required": True,
             "requirement": "Core flow works", "method": "Exercise the core flow",
             "target": "Expected output", "applicability": "Local demo"},
            {"id": "extra", "source": "Optional improvement", "required": False,
             "requirement": "Additional styling", "method": "Inspect preview",
             "target": "Agreed appearance", "applicability": "Local demo"}]}
        self.contract_path = self.root / "contract.json"
        self.write_contract()
        self.call("init", "--project-root", str(self.root), "--contract", str(self.contract_path),
                  "--decision", "Fixture agreement")

    def write_contract(self):
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")

    def call(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--state", str(self.state), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr + result.stdout)
        return json.loads(result.stdout if ok else result.stderr)

    def start(self, version="v1", ok=True):
        return self.call("start", "--version", version, "--artifact", "product.txt", ok=ok)

    def record(self, verdict="pass", condition="core", evidence=True, ok=True, decision=None):
        args = ["record", "--condition", condition, "--verdict", verdict,
                "--method", "Inspect output", "--note", "Observed result recorded",
                "--review-mode", "shared_context"]
        if evidence:
            args.extend(["--evidence", "check.log"])
        if decision:
            args.extend(["--decision", decision])
        return self.call(*args, ok=ok)

    def test_complete_flow_and_resume_in_new_process(self):
        self.assertEqual(self.call("status")["unmet_required"], ["core"])
        self.start()
        self.record("fail")
        self.artifact.write_text("fixed version", encoding="utf-8")
        self.start("v2")
        self.record()
        result = self.call("checkpoint", "--phase", "user_feedback", "--next-action",
                           "Present checked result", "--note", "사용자 의견을 기다립니다")
        self.assertEqual(result["status"], "ready_for_user_review")
        restored = self.call("status")
        self.assertEqual(restored["iteration"], 2)
        self.assertTrue(restored["checkpoint_matches_current_iteration"])
        self.assertEqual(restored["checkpoint"]["note"], "사용자 의견을 기다립니다")
        events = self.call("history")
        self.assertEqual([e["detail"]["verdict"] for e in events if e["event"] == "record"],
                         ["fail", "pass"])

    def test_no_pass_without_evidence_or_missing_evidence(self):
        self.start()
        self.assertIn("requires evidence", self.record(evidence=False, ok=False)["error"])
        self.evidence.unlink()
        self.assertIn("does not exist", self.record(ok=False)["error"])
        self.assertEqual(self.call("status")["unmet_required"], ["core"])

    def test_optional_pass_cannot_hide_required_failure(self):
        self.start()
        self.record("fail")
        result = self.record(condition="extra")
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["unmet_required"], ["core"])

    def test_changed_artifact_invalidates_previous_pass(self):
        self.start()
        self.record()
        self.artifact.write_text("changed without review", encoding="utf-8")
        result = self.call("status")
        self.assertEqual(result["conditions"][0]["reason"], "artifact_changed_or_missing")
        self.record(ok=False)
        self.start("v2")
        self.assertEqual(self.call("status")["conditions"][0]["verdict"], "unverified")

    def test_changed_and_deleted_evidence_invalidate_pass(self):
        self.start()
        self.record()
        self.evidence.write_text("replaced log", encoding="utf-8")
        self.assertEqual(self.call("status")["conditions"][0]["reason"], "evidence_changed_or_missing")
        self.record()
        self.evidence.unlink()
        self.assertEqual(self.call("status")["conditions"][0]["verdict"], "unverified")

    def test_required_waiver_rejected_and_optional_waiver_traced(self):
        self.start()
        self.record("waived", decision="Fixture decision", ok=False)
        self.record("waived", condition="extra", ok=False)
        result = self.record("waived", condition="extra", decision="Fixture decision")
        self.assertEqual(result["conditions"][1]["verdict"], "waived")
        self.assertEqual(result["unmet_required"], ["core"])

    def test_iteration_limit_does_not_pass_or_mutate(self):
        self.start()
        result = self.start("v2")
        self.assertEqual(result["status"], "limit_reached")
        before = self.state.read_bytes()
        self.assertIn("limit reached", self.start("v3", ok=False)["error"])
        self.assertEqual(self.state.read_bytes(), before)

    def test_contract_revision_keeps_history_and_invalidates_results(self):
        self.start()
        self.record()
        self.contract["conditions"][0]["target"] = "New agreed output"
        self.write_contract()
        result = self.call("contract", "--contract", str(self.contract_path),
                           "--decision", "User revised the target")
        self.assertEqual(result["conditions"][0]["reason"], "contract_changed")
        self.record(ok=False)
        self.assertEqual(self.call("history")[0]["detail"]["contract"]["conditions"][0]["target"],
                         "Expected output")

    def test_reinit_and_invalid_contract_do_not_overwrite(self):
        before = self.state.read_bytes()
        self.call("init", "--project-root", str(self.root), "--contract", str(self.contract_path),
                  "--decision", "Fixture", ok=False)
        self.assertEqual(self.state.read_bytes(), before)
        self.contract["conditions"][0]["required"] = "false"
        self.write_contract()
        self.call("contract", "--contract", str(self.contract_path), "--decision", "Fixture", ok=False)
        self.assertEqual(self.state.read_bytes(), before)

    def test_missing_iteration_and_unknown_condition_rejected(self):
        self.record(ok=False)
        self.start()
        self.record(condition="unknown", ok=False)


if __name__ == "__main__":
    unittest.main()
