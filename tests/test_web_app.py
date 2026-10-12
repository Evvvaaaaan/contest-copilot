"""HTTP and subprocess integration checks using a clearly marked CLI test double."""

import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("contest_web", ROOT / "web/server.py")
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class WebFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        fake = self.root / "codex-test-double"
        fake.write_text(f"#!{sys.executable}\n" + (ROOT / "tests/fixtures/fake_codex.py").read_text())
        fake.chmod(0o700)
        self.app = web.App(self.root / "data", codex=str(fake), turn_timeout=10)
        self.server = web.make_server(self.app, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.token = self.request("/api/session")["token"]
        self.project = self.request("/api/projects", {"title": "테스트 공모전"})["id"]

    def tearDown(self):
        for project_id in list(self.app.jobs):
            self.app.stop(project_id)
        deadline = time.monotonic() + 6
        while self.app.jobs and time.monotonic() < deadline:
            time.sleep(0.05)
        # Ensure a failed cancellation test never leaves a fixture process behind.
        for job in self.app.jobs.values():
            if job["process"] and job["process"].poll() is None:
                job["process"].kill()
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def request(self, path, body=None, headers=None, expected=None):
        data = None if body is None else json.dumps(body).encode()
        request_headers = {"X-Local-Token": getattr(self, "token", ""), "Content-Type": "application/json"}
        request_headers.update(headers or {})
        request = Request(self.base + path, data=data, headers=request_headers)
        try:
            with urlopen(request, timeout=12) as response:
                payload = response.read()
                if expected is not None:
                    self.assertEqual(response.status, expected)
                return json.loads(payload) if "application/json" in response.headers["Content-Type"] else payload
        except HTTPError as error:
            with error:
                self.assertEqual(error.code, expected, error.read().decode())
            return None

    def wait(self, status="idle", seconds=6):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            result = self.request(f"/api/projects/{self.project}")
            if result["status"] == status and self.project not in self.app.jobs:
                return result
            time.sleep(0.05)
        self.fail(f"Run did not reach {status}")

    def test_static_app_and_empty_state(self):
        self.assertIn("아이디어는 당신에게서".encode(), self.request("/"))
        self.assertIn(b"async function api", self.request("/app.js"))
        state = self.request(f"/api/projects/{self.project}")
        self.assertIsNone(state["progress"])
        self.assertEqual(state["messages"], [])

    def test_real_http_transport_and_thread_resume_with_fixture(self):
        self.request(f"/api/projects/{self.project}/message", {"text": "First message"}, expected=202)
        first = self.wait()
        self.assertEqual(first["messages"][-1]["text"], "Fixture first response")
        self.assertEqual(first["phase"], "research")
        self.request(f"/api/projects/{self.project}/message", {"text": "Second message"})
        second = self.wait()
        self.assertEqual(second["messages"][-1]["text"], "Fixture resumed response")
        self.assertEqual(len(second["messages"]), 4)
        restarted = web.App(self.app.root, codex=self.app.codex)
        self.assertEqual(restarted.load(self.project)["messages"], second["messages"])

    def test_failed_turn_is_never_shown_as_success(self):
        self.request(f"/api/projects/{self.project}/message", {"text": "TEST_FAIL"})
        result = self.wait("failed")
        self.assertEqual(result["messages"][-1]["role"], "error")
        self.assertIn("Intentional fixture failure", result["messages"][-1]["text"])

    def test_stop_terminates_unresponsive_worker(self):
        self.request(f"/api/projects/{self.project}/message", {"text": "TEST_WAIT"})
        time.sleep(0.3)
        self.request(f"/api/projects/{self.project}/message", {"text": "duplicate"}, expected=400)
        self.request(f"/api/projects/{self.project}/stop", {})
        result = self.wait("interrupted", seconds=5)
        self.assertEqual(len(result["messages"]), 1)

    def test_stop_wait_survives_forward_wall_clock_jump(self):
        self.request(f"/api/projects/{self.project}/message", {"text": "TEST_WAIT"})
        time.sleep(0.3)
        self.request(f"/api/projects/{self.project}/stop", {})
        wall = time.time()
        calls = iter((wall, wall + 3600))
        jumping_clock = SimpleNamespace(time=lambda: next(calls, wall + 3600),
                                        monotonic=time.monotonic, sleep=time.sleep)
        # Patch this test module only, preserving real server/process clocks.
        with mock.patch.dict(globals(), time=jumping_clock):
            result = self.wait("interrupted", seconds=5)
        self.assertEqual(result["status"], "interrupted")
        self.assertNotIn(self.project, self.app.jobs)

    def test_upload_download_and_no_path_escape(self):
        upload = self.request(f"/api/projects/{self.project}/upload", {
            "name": "공고.txt", "data": base64.b64encode("공고 내용".encode()).decode()})
        from urllib.parse import quote
        result = self.request(f"/api/projects/{self.project}/file?path=" + quote(upload["path"]))
        self.assertEqual(result.decode(), "공고 내용")
        self.request(f"/api/projects/{self.project}/file?path=../../chat.json", expected=404)
        self.request(f"/api/projects/{self.project}/upload", {"name": "../bad", "data": "eA=="}, expected=400)

    def test_timeout_terminates_child_after_parent_exit(self):
        self.app.timeout = 1
        self.request(f"/api/projects/{self.project}/message", {"text": "TEST_ORPHAN"})
        result = self.wait("interrupted", seconds=5)
        self.assertIn("시간 한도", result["activity"])

    def test_upload_cannot_follow_workspace_symlink(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.app.directory(self.project) / "workspace/inputs").symlink_to(outside)
        self.request(f"/api/projects/{self.project}/upload", {"name": "bad.txt", "data": "eA=="}, expected=400)
        self.assertEqual(list(outside.iterdir()), [])

    def test_foreign_origin_and_wrong_token_are_rejected(self):
        self.request("/api/session", headers={"Origin": "https://example.org"}, expected=403)
        self.request("/api/session", headers={"Host": "example.org"}, expected=403)
        self.request("/api/projects", {"title": "bad"}, headers={"X-Local-Token": "wrong"}, expected=403)

    def test_progress_uses_real_state_helper_and_file_freshness(self):
        workspace = self.app.directory(self.project) / "workspace"
        contract = {"project": "Fixture", "intent": "Test evidence display", "max_iterations": 2,
                    "conditions": [{"id": "core", "source": "Fixture", "required": True,
                    "requirement": "Expected output", "method": "Inspect", "target": "Matches", "applicability": "Fixture"}]}
        (workspace / "contract.json").write_text(json.dumps(contract))
        (workspace / "product.txt").write_text("v1")
        (workspace / "evidence.log").write_text("Checked")
        command = [sys.executable, str(ROOT / "contest-copilot/scripts/manage_state.py"), "--state", str(workspace / "progress.json")]
        steps = [["init", "--contract", "contract.json", "--project-root", str(workspace), "--decision", "Fixture agreement"],
                 ["start", "--version", "v1", "--artifact", "product.txt"],
                 ["record", "--condition", "core", "--verdict", "pass", "--method", "Inspect", "--note", "Observed",
                  "--review-mode", "shared_context", "--evidence", "evidence.log"]]
        for step in steps:
            subprocess.run(command + step, cwd=workspace, capture_output=True, check=True)
        reported = self.request(f"/api/projects/{self.project}")["progress"]
        self.assertEqual(reported["status"], "ready_for_user_review")
        self.assertEqual(reported["conditions"][0]["target"], "Matches")
        subprocess.run(command + ["checkpoint", "--phase", "user_feedback", "--next-action", "Review v1", "--note", "Fixture"],
                       cwd=workspace, capture_output=True, check=True)
        (workspace / "product.txt").write_text("changed")
        self.assertEqual(self.request(f"/api/projects/{self.project}")["progress"]["unmet_required"], ["core"])
        subprocess.run(command + ["start", "--version", "v2", "--artifact", "product.txt"],
                       cwd=workspace, capture_output=True, check=True)
        (workspace / "ui-state.json").write_text(json.dumps({"phase": "development", "next_action": "Check v2"}))
        self.assertEqual(self.request(f"/api/projects/{self.project}")["phase"], "development")

    def test_restart_marks_inflight_work_interrupted(self):
        self.app.update(self.project, status="running")
        restarted = web.App(self.app.root, codex=self.app.codex)
        self.assertEqual(restarted.load(self.project)["status"], "interrupted")


if __name__ == "__main__":
    unittest.main()
