"""Exercise actual submission generation and evidence/version rejection."""

import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPTS = Path(__file__).resolve().parents[1] / "contest-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_submission


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "product.py").write_text("print('real artifact')\n")
        (self.root / "evidence.txt").write_text("Observed: real artifact\n")
        def capture(name):
            path = self.root / name
            return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        self.evidence = capture("evidence.txt")
        self.state = {"schema_version": 1, "project_root": str(self.root), "contract_version": 1,
                      "contract": {"project": "Example", "intent": "Test", "max_iterations": 2,
                                   "conditions": [{"id": "core", "required": True, "source": "official notice",
                                                   "requirement": "Core works", "method": "Run", "target": "real artifact",
                                                   "applicability": "Product"}]}, "checkpoint": None,
                      "iterations": [{"number": 1, "artifact_version": "v1", "contract_version": 1,
                                      "artifacts": [capture("product.py")],
                                      "results": {"core": {"verdict": "pass", "evidence": [self.evidence]}}}]}
        self.save_state()
        self.records = {"sources": [{"id": "notice", "status": "inspected", "title": "Official notice", "url": "https://example.org"}],
                        "decisions": [{"id": "d1", "actor": "user", "original": "My idea", "revised": "My revised idea", "reason": "Needs evidence"}]}
        (self.root / "records.json").write_text(json.dumps(self.records))
        self.spec = {"project": "Example", "title": "Report",
                     "official_instructions": [{"id": "r1", "text": "Working product", "source_id": "notice", "condition_ids": ["core"]}],
                     "accepted": {"artifact_version": "v1", "contract_version": 1, "iteration": 1, "decision_reference": "message-17"},
                     "sections": [{"title": "Results", "claims": [{"kind": "measured", "text": "Output observed", "source_ids": ["notice"],
                                                                    "evidence": [{**self.evidence, "path": "evidence.txt"}]}]}],
                     "formats": [{"format": "md", "filename": "report.md"}, {"format": "html", "filename": "report.html"}],
                     "user_decision_ids": ["d1"]}

    def save_state(self):
        (self.root / "progress.json").write_text(json.dumps(self.state))

    def test_cli_generates_readable_outputs_manifest_and_contributions(self):
        spec_path = self.root / "spec.json"
        spec_path.write_text(json.dumps(self.spec))
        result = subprocess.run([sys.executable, str(SCRIPTS / "build_submission.py"), "--workspace", str(self.root), "--spec", str(spec_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(result.stdout)
        self.assertEqual(manifest["status"], "ready_for_local_review")
        self.assertFalse(manifest["externally_submitted"])
        report = (self.root / "submission/report.md").read_text()
        self.assertIn("측정 결과", report)
        self.assertIn("My revised idea", report)
        for output in manifest["outputs"]:
            content = (self.root / "submission" / output["filename"]).read_bytes()
            self.assertEqual(len(content), output["bytes"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), output["sha256"])

    def test_missing_claim_evidence_and_bad_hash_rejected(self):
        claim = self.spec["sections"][0]["claims"][0]
        original = copy.deepcopy(claim["evidence"])
        claim["evidence"] = []
        with self.assertRaisesRegex(ValueError, "require evidence"):
            build_submission.build(self.root, self.spec)
        claim["evidence"] = original
        claim["evidence"][0]["sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "hash"):
            build_submission.build(self.root, self.spec)

    def test_stale_acceptance_and_changed_artifact_rejected(self):
        self.spec["accepted"]["iteration"] = 2
        with self.assertRaisesRegex(ValueError, "Stale acceptance"):
            build_submission.build(self.root, self.spec)
        self.spec["accepted"]["iteration"] = 1
        (self.root / "product.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "currently pass"):
            build_submission.build(self.root, self.spec)

    def test_missing_acceptance_reference_rejected(self):
        self.spec["accepted"]["decision_reference"] = ""
        with self.assertRaisesRegex(ValueError, "decision reference"):
            build_submission.build(self.root, self.spec)

    def test_html_escapes_script_and_attribute_injection(self):
        attack = '<script>alert("x")</script><img src=x onerror="alert(1)">'
        self.spec["title"] = attack
        self.spec["sections"][0]["claims"][0]["text"] = attack
        build_submission.build(self.root, self.spec)
        rendered = (self.root / "submission/report.html").read_text()
        self.assertNotIn("<script", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_html_has_semantic_sections_and_readable_record_fields(self):
        self.records["sources"][0].update(locator="Section 2", accessed_at="2026-10-12")
        self.records["decisions"][0]["message_ref"] = "message-3"
        (self.root / "records.json").write_text(json.dumps(self.records))
        build_submission.build(self.root, self.spec)
        rendered = (self.root / "submission/report.html").read_text()
        self.assertIn("<h1>Report</h1>", rendered)
        self.assertIn("<h2>Results</h2>", rendered)
        self.assertIn("<strong>측정 결과</strong>", rendered)
        self.assertIn("<strong>처음 생각</strong>: My idea", rendered)
        self.assertIn("<strong>대화 참조</strong>: message-3", rendered)
        self.assertIn("Official notice [notice]", rendered)
        self.assertIn("<strong>주소</strong>: https://example.org", rendered)
        self.assertIn("<strong>원문 위치</strong>: Section 2", rendered)
        self.assertNotIn("<pre>", rendered)
        self.assertNotIn("## Results", rendered)
        self.assertNotIn("**측정 결과**", rendered)
        self.assertNotIn('&quot;actor&quot;:', rendered)
        markdown = (self.root / "submission/report.md").read_text()
        self.assertIn("## Results", markdown)
        self.assertIn("**측정 결과**", markdown)

    def test_record_and_title_markup_cannot_create_active_html(self):
        payload = '</li><script>alert(1)</script><img src=x onerror=alert(2)>'
        self.spec["title"] = "{{content}} " + payload
        self.records["sources"][0]["title"] = payload
        self.records["sources"][0]["url"] = 'javascript:alert(3)'
        self.records["decisions"][0]["original"] = payload
        (self.root / "records.json").write_text(json.dumps(self.records))
        build_submission.build(self.root, self.spec)
        rendered = (self.root / "submission/report.html").read_text()
        tags = []
        class Inspector(HTMLParser):
            def handle_starttag(self, tag, attrs):
                tags.append(tag)
        Inspector().feed(rendered)
        self.assertNotIn("script", tags)
        self.assertNotIn("img", tags)
        self.assertNotIn("a", tags)
        self.assertEqual(tags.count("h1"), 1)
        self.assertIn("{{content}} &lt;/li&gt;", rendered)

    def test_only_requested_formats_and_real_zip(self):
        build_submission.build(self.root, self.spec)
        self.spec["formats"] = [{"format": "zip", "filename": "source.zip"}]
        self.spec["source_files"] = ["product.py"]
        manifest = build_submission.build(self.root, self.spec)
        self.assertEqual(manifest["status"], "ready_for_local_review")
        self.assertFalse((self.root / "submission/report.md").exists())
        with zipfile.ZipFile(self.root / "submission/source.zip") as archive:
            self.assertEqual(archive.namelist(), ["product.py"])
            self.assertEqual(archive.read("product.py"), (self.root / "product.py").read_bytes())

    def test_rebuild_preserves_user_edits(self):
        build_submission.build(self.root, self.spec)
        report = self.root / "submission/report.md"
        report.write_text("User edits")
        with self.assertRaisesRegex(ValueError, "edited"):
            build_submission.build(self.root, self.spec)
        self.assertEqual(report.read_text(), "User edits")

    def test_source_zip_rejects_traversal_absolute_and_symlink_escape(self):
        self.spec["formats"] = [{"format": "zip", "filename": "source.zip"}]
        (self.root / "escape").symlink_to(self.root.parent)
        for raw in ("../outside.txt", "/etc/passwd", "escape/outside.txt"):
            with self.subTest(path=raw):
                self.spec["source_files"] = [raw]
                with self.assertRaises(ValueError):
                    build_submission.build(self.root, self.spec)

    def test_official_missing_checks_unsupported_formats_and_limits_block(self):
        self.spec["official_instructions"][0]["condition_ids"] = []
        self.spec["formats"] = [{"format": "pptx", "filename": "slides.pptx"},
                                {"format": "html", "filename": "report.html", "max_bytes": 1, "max_pages": 2}]
        manifest = build_submission.build(self.root, self.spec)
        self.assertEqual(manifest["status"], "not_ready")
        reasons = {item["reason"] for item in manifest["blockers"]}
        self.assertEqual(reasons, {"official_requirement_not_verified", "unsupported_format", "size_limit_exceeded", "page_count_requires_rendered_format_check"})
        self.assertFalse((self.root / "submission/slides.pptx").exists())

    def test_unknown_source_and_assistant_contribution_rejected(self):
        self.spec["sections"][0]["claims"][0]["source_ids"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "Unknown source"):
            build_submission.build(self.root, self.spec)
        self.spec["sections"][0]["claims"][0]["source_ids"] = ["notice"]
        self.records["decisions"][0]["actor"] = "assistant"
        (self.root / "records.json").write_text(json.dumps(self.records))
        with self.assertRaisesRegex(ValueError, "not attributed"):
            build_submission.build(self.root, self.spec)

    def test_changed_local_source_rejected(self):
        self.records["sources"][0].update({"path": "product.py", "sha256": "old-hash"})
        (self.root / "records.json").write_text(json.dumps(self.records))
        with self.assertRaisesRegex(ValueError, "Source file changed"):
            build_submission.build(self.root, self.spec)


if __name__ == "__main__":
    unittest.main()
