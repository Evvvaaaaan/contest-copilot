"""Verify persisted provenance, extraction coverage and CLI isolation."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'contest-copilot/scripts/project_records.py'
spec = importlib.util.spec_from_file_location('project_records', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.records = module.Records(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def source(self, **updates):
        value = {'title': 'Official notice', 'url': 'https://example.org/notice',
                 'status': 'inspected', 'locator': 'Eligibility, paragraph 2',
                 'accessed_at': '2026-10-12', 'excerpt': 'Applicants must be students.'}
        value.update(updates)
        return self.records.add_source(value)

    def test_facts_require_inspected_known_sources(self):
        source = self.source(status='discovered')
        claim = {'kind': 'fact', 'text': 'Students may apply.', 'uncertainty': 'No ambiguity found.',
                 'source_ids': [source['id']]}
        with self.assertRaisesRegex(ValueError, 'inspected'):
            self.records.add_claim(claim)
        source['status'] = 'inspected'
        self.records.add_source(source)
        saved = self.records.add_claim(claim)
        self.assertEqual(saved['source_revisions'][source['id']], 2)
        claim['source_ids'] = ['unknown']
        with self.assertRaisesRegex(ValueError, 'unknown'):
            self.records.add_claim(claim)
        self.assertEqual(len(self.records.read()['claims']), 1)

    def test_source_revision_preserves_original_and_stable_id(self):
        first = self.source()
        updated = self.source(id=first['id'], excerpt='Amended eligibility requirements.')
        state = module.Records(self.root).read()
        self.assertEqual(updated['revision'], 2)
        self.assertEqual(updated['id'], first['id'])
        self.assertEqual(len(state['sources']), 1)
        self.assertEqual(state['history'][-1]['previous'], first)
        self.assertEqual(state['history'][0]['record'], first)

    def test_decision_actor_and_original_preserved_without_authentication(self):
        decision = {'actor': 'user', 'original': 'Chatbot', 'revised': 'Notification app',
                    'reason': 'Prevent missed deadlines', 'message_ref': 'message-7',
                    'approval_authenticated': True}
        result = self.records.add_decision(decision)
        self.assertFalse(result['approval_authenticated'])
        self.assertEqual(result['original'], 'Chatbot')
        decision['actor'] = 'system'
        with self.assertRaises(ValueError):
            self.records.add_decision(decision)
        self.assertEqual(len(self.records.read()['decisions']), 1)

    def test_path_traversal_absolute_and_symlink_escape_rejected(self):
        outside = self.root.parent / (self.root.name + '-outside.txt')
        outside.write_text('private', encoding='utf-8')
        try:
            (self.root / 'escape.txt').symlink_to(outside)
            for path in ('../' + outside.name, str(outside), 'escape.txt'):
                with self.assertRaises(ValueError):
                    self.records.extract(path)
            with self.assertRaises(ValueError):
                self.source(path='escape.txt')
        finally:
            outside.unlink()

    def test_text_hash_and_logical_sections_survive_new_process(self):
        (self.root / 'notice.md').write_text('# 지원 자격\n학생', encoding='utf-8')
        result = self.records.extract('notice.md')
        self.assertEqual(result['status'], 'extracted')
        self.assertTrue(result['coverage_complete'])
        self.assertEqual(result['pagination'], 'logical_section')
        self.assertIn('학생', result['pages'][0]['text'])
        (self.root / 'notice.md').write_text('Revised', encoding='utf-8')
        revised = self.records.extract('notice.md')
        self.assertNotEqual(result['sha256'], revised['sha256'])
        output = subprocess.run([sys.executable, str(SCRIPT), '--workspace', str(self.root), 'show'],
                                capture_output=True, text=True, check=True)
        self.assertEqual(len(json.loads(output.stdout)['documents']), 2)

    def test_html_excludes_script_and_discloses_visual_gap(self):
        (self.root / 'notice.html').write_text('<h1>Notice</h1><script>hidden()</script><p>Student &amp; teacher</p>')
        result = self.records.extract('notice.html')
        self.assertIn('Student & teacher', result['pages'][0]['text'])
        self.assertNotIn('hidden', result['pages'][0]['text'])
        self.assertFalse(result['coverage_complete'])

    def test_docx_main_text_is_partial_not_full_rendering(self):
        with zipfile.ZipFile(self.root / 'notice.docx', 'w') as archive:
            archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Eligibility</w:t></w:r></w:p></w:body></w:document>')
        result = self.records.extract('notice.docx')
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['pages'][0]['text'], 'Eligibility')
        self.assertFalse(result['coverage_complete'])

    def test_unsupported_and_bad_encoding_explicitly_unavailable(self):
        for name, data in [('notice.hwp', b'hwp'), ('bad.txt', b'\xff\xfe\x00')]:
            (self.root / name).write_bytes(data)
            result = self.records.extract(name)
            self.assertEqual(result['status'], 'unavailable')
            self.assertTrue(result['limitations'])
            self.assertFalse(result['coverage_complete'])

    def test_pdf_without_backend_reports_unknown_coverage(self):
        (self.root / 'notice.pdf').write_bytes(b'%PDF-1.4')
        with patch.dict(sys.modules, {'pypdf': None}), patch.object(module.shutil, 'which', return_value=None):
            result = self.records.extract('notice.pdf')
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['pages'], [])
        self.assertTrue(any('unknown' in x for x in result['limitations']))

    def test_pdf_empty_page_is_reported_and_not_counted_as_read(self):
        (self.root / 'notice.pdf').write_bytes(b'%PDF-1.4')
        output = subprocess.CompletedProcess([], 0, b'First page\f\fThird page\f', b'')
        with patch.dict(sys.modules, {'pypdf': None}), patch.object(module.shutil, 'which', return_value='/usr/bin/pdftotext'), patch.object(module.subprocess, 'run', return_value=output):
            result = self.records.extract('notice.pdf')
        self.assertEqual(result['status'], 'partial')
        self.assertEqual([page['page'] for page in result['pages']], [1, 2, 3])
        self.assertEqual(result['pages'][1]['status'], 'needs_ocr_or_empty')

    def test_real_pdf_backend_reads_text_and_marks_blank_page(self):
        if not module.shutil.which('pdftotext') and importlib.util.find_spec('pypdf') is None:
            self.skipTest('Optional PDF backends are not installed.')
        stream = b'BT /F1 12 Tf 72 720 Td (Eligibility) Tj ET'
        objects = [
            b'<< /Type /Catalog /Pages 2 0 R >>',
            b'<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
            b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> >>',
        ]
        pdf = bytearray(b'%PDF-1.4\n')
        offsets = [0]
        for index, obj in enumerate(objects, 1):
            offsets.append(len(pdf))
            pdf.extend(f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n')
        start = len(pdf)
        pdf.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
        for offset in offsets[1:]:
            pdf.extend(f'{offset:010} 00000 n \n'.encode())
        pdf.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
        (self.root / 'actual.pdf').write_bytes(pdf)
        result = self.records.extract('actual.pdf')
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(len(result['pages']), 2)
        self.assertIn('Eligibility', result['pages'][0]['text'])
        self.assertEqual(result['pages'][1]['status'], 'needs_ocr_or_empty')

    def test_concurrent_cli_writers_keep_every_record(self):
        processes = []
        for index in range(6):
            payload = self.root / f'input-{index}.json'
            payload.write_text(json.dumps({'title': f'Source {index}', 'url': 'https://example.org', 'status': 'discovered'}))
            processes.append(subprocess.Popen([sys.executable, str(SCRIPT), '--workspace', str(self.root),
                                               'source', '--input', str(payload)], stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIn('id', json.loads(stdout))
        state = self.records.read()
        self.assertEqual(len(state['sources']), 6)
        self.assertEqual(len({entry['id'] for entry in state['sources']}), 6)
        self.assertEqual(len(state['history']), 6)

    def test_failed_cli_returns_nonzero_without_records(self):
        payload = self.root / 'invalid.json'
        payload.write_text('{}')
        result = subprocess.run([sys.executable, str(SCRIPT), '--workspace', str(self.root),
                                 'decision', '--input', str(payload)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('error', json.loads(result.stderr))
        self.assertEqual(self.records.read()['decisions'], [])


if __name__ == '__main__':
    unittest.main()
