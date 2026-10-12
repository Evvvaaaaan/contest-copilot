#!/usr/bin/env python3
"""Keep traceable research, decisions and document extraction in a local workspace.

These records preserve supplied assertions, not authenticated user approvals.
Python 3.9+, macOS/Linux. PDF extraction optionally uses pdftotext or pypdf.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile


def required(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a nonempty string.")
    return value


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        elif tag in ('p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'tr'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


class Records:
    def __init__(self, workspace):
        self.root = Path(workspace).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self._path('records.json')
        self.lock_path = self._path('.records.lock')

    def _path(self, relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError('Use a relative workspace path.')
        path = (self.root / relative).resolve()
        if self.root not in path.parents:
            raise ValueError('Path escapes the workspace.')
        return path

    def _load(self):
        if not self.path.exists():
            return {'schema_version': 1, 'sources': [], 'claims': [],
                    'decisions': [], 'documents': [], 'history': []}
        state = json.loads(self.path.read_text(encoding='utf-8'))
        if state.get('schema_version') != 1:
            raise ValueError('Unsupported records schema.')
        return state

    def read(self):
        with self.lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            return self._load()

    def _save(self, state):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', dir=self.root, encoding='utf-8',
                                             prefix='.records-', delete=False) as stream:
                temporary = stream.name
                json.dump(state, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def _put(self, collection, data, validate):
        if not isinstance(data, dict):
            raise ValueError('Record must be an object.')
        entry = deepcopy(data)
        with self.lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = self._load()
            validate(entry, state)
            identifier = entry.get('id')
            previous = next((x for x in state[collection] if x['id'] == identifier), None)
            if identifier is not None and previous is None:
                raise ValueError('Unknown record ID; omit id when creating a record.')
            entry['id'] = identifier or collection.rstrip('s') + '-' + uuid.uuid4().hex[:12]
            entry['created_at'] = previous['created_at'] if previous else datetime.now(timezone.utc).isoformat()
            entry['updated_at'] = datetime.now(timezone.utc).isoformat()
            entry['revision'] = previous['revision'] + 1 if previous else 1
            if previous:
                state[collection][state[collection].index(previous)] = entry
            else:
                state[collection].append(entry)
            state['history'].append({'collection': collection, 'id': entry['id'],
                                     'at': entry['updated_at'], 'previous': previous,
                                     'record': deepcopy(entry)})
            self._save(state)
            return entry

    def add_source(self, data):
        def validate(entry, state):
            required(entry, 'title')
            if not entry.get('url') and not entry.get('path'):
                raise ValueError('A source needs url or path.')
            if entry.get('url') and (not isinstance(entry['url'], str) or
                                     not entry['url'].startswith(('https://', 'http://'))):
                raise ValueError('Source URL must use http or https.')
            if entry.get('path'):
                path = self._path(entry['path'])
                if not path.is_file():
                    raise ValueError('Source file does not exist.')
                entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            if entry.get('status') not in ('discovered', 'inspected'):
                raise ValueError('Source status must be discovered or inspected.')
            if entry['status'] == 'inspected':
                for key in ('locator', 'accessed_at', 'excerpt'):
                    required(entry, key)
            for key in ('locator', 'accessed_at', 'published_at', 'excerpt', 'evidence'):
                entry.setdefault(key, '')
        return self._put('sources', data, validate)

    def add_claim(self, data):
        def validate(entry, state):
            required(entry, 'text')
            required(entry, 'uncertainty')
            if entry.get('kind') not in ('fact', 'interpretation', 'prediction'):
                raise ValueError('Claim kind must be fact, interpretation or prediction.')
            links = entry.get('source_ids')
            if not isinstance(links, list) or not links or any(not isinstance(x, str) for x in links):
                raise ValueError('A claim requires source_ids.')
            sources = {x['id']: x for x in state['sources']}
            if any(x not in sources for x in links):
                raise ValueError('Claim references an unknown source.')
            if entry['kind'] == 'fact' and any(sources[x]['status'] != 'inspected' for x in links):
                raise ValueError('A factual claim must cite inspected sources.')
            entry['source_revisions'] = {x: sources[x]['revision'] for x in links}
        return self._put('claims', data, validate)

    def add_decision(self, data):
        def validate(entry, state):
            if entry.get('actor') not in ('user', 'assistant'):
                raise ValueError('Decision actor must be user or assistant.')
            for key in ('original', 'revised', 'reason', 'message_ref'):
                required(entry, key)
            entry['approval_authenticated'] = False
        return self._put('decisions', data, validate)

    def extract(self, relative_path):
        path = self._path(relative_path)
        if path == self.path or path == self.lock_path:
            raise ValueError('Records metadata cannot be extracted as source material.')
        content = path.read_bytes()
        if len(content) > 32 * 1024 * 1024:
            raise ValueError('Document exceeds the 32 MiB extraction limit.')
        entry = {'path': str(path.relative_to(self.root)),
                 'sha256': hashlib.sha256(content).hexdigest(), 'pages': [],
                 'status': 'unavailable', 'backend': None, 'pagination': 'unknown',
                 'limitations': [], 'coverage_complete': False}
        extension = path.suffix.lower()
        try:
            if extension in ('.txt', '.md', '.csv', '.json', '.html', '.htm'):
                text = content.decode('utf-8-sig')
                if extension in ('.html', '.htm'):
                    parser = HTMLText()
                    parser.feed(text)
                    text = ''.join(parser.parts)
                entry.update(backend='stdlib', pagination='logical_section')
                entry['pages'] = [self._page(1, text)]
                entry['limitations'].append('Logical text section; not a rendered page. Images are not read.')
            elif extension == '.docx':
                with zipfile.ZipFile(path) as archive:
                    info = archive.getinfo('word/document.xml')
                    if info.file_size > 32 * 1024 * 1024:
                        raise ValueError('DOCX XML exceeds the extraction limit.')
                    tree = ET.fromstring(archive.read(info))
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text = '\n'.join(''.join(p.itertext()) for p in tree.findall('.//w:p', ns))
                entry.update(backend='stdlib-docx', pagination='logical_section')
                entry['pages'] = [self._page(1, text)]
                entry['limitations'].append('Main document text only; headers, comments, images and rendered pagination are not inspected.')
            elif extension == '.pdf':
                self._pdf(path, entry)
            else:
                entry['limitations'].append(f'Unsupported format: {extension or "no extension"}. Provide a text or PDF export.')
        except (OSError, ValueError, UnicodeError, ET.ParseError, zipfile.BadZipFile,
                KeyError, subprocess.SubprocessError) as error:
            entry['limitations'].append(str(error))
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Document changed during extraction; retry against a stable file.')
        if entry['pages']:
            readable = sum(page['status'] == 'extracted' for page in entry['pages'])
            entry['status'] = 'extracted' if readable == len(entry['pages']) else ('partial' if readable else 'unavailable')
            if entry['limitations'] and entry['backend'] == 'stdlib-docx' and readable:
                entry['status'] = 'partial'
            entry['coverage_complete'] = bool(entry['status'] == 'extracted' and extension in ('.txt', '.md', '.csv', '.json'))
        return self._put('documents', entry, lambda value, state: None)

    @staticmethod
    def _page(number, text):
        return {'page': number, 'text': text.strip(),
                'status': 'extracted' if text.strip() else 'needs_ocr_or_empty'}

    def _pdf(self, path, entry):
        entry['pagination'] = 'physical_page'
        entry['limitations'].append('Text extraction only; images, charts and reading order need visual inspection. No OCR performed.')
        try:
            from pypdf import PdfReader
        except ImportError:
            PdfReader = None
        if PdfReader:
            entry['backend'] = 'pypdf'
            try:
                reader = PdfReader(str(path))
                for number, page in enumerate(reader.pages, 1):
                    try:
                        entry['pages'].append(self._page(number, page.extract_text() or ''))
                    except Exception as error:
                        entry['pages'].append({'page': number, 'text': '', 'status': 'unavailable', 'error': str(error)})
                return
            except Exception as error:
                entry['limitations'].append(f'pypdf failed: {error}')
        if not shutil.which('pdftotext'):
            entry['limitations'].append('PDF backend unavailable; install pdftotext or pypdf. Page count and coverage are unknown.')
            return
        entry['backend'] = 'pdftotext'
        result = subprocess.run(['pdftotext', '-enc', 'UTF-8', str(path), '-'],
                                capture_output=True, timeout=60, check=True)
        sections = result.stdout.decode('utf-8').split('\f')
        if sections and not sections[-1].strip():
            sections.pop()
        entry['pages'] = [self._page(n, text) for n, text in enumerate(sections, 1)]
        if result.stderr:
            entry['limitations'].append(result.stderr.decode('utf-8', errors='replace').strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('source', 'claim', 'decision'):
        commands.add_parser(name).add_argument('--input', required=True)
    commands.add_parser('extract').add_argument('--file', required=True)
    commands.add_parser('show')
    args = parser.parse_args()
    try:
        records = Records(args.workspace)
        if args.command == 'show':
            result = records.read()
        elif args.command == 'extract':
            result = records.extract(args.file)
        else:
            data = json.loads(Path(args.input).read_text(encoding='utf-8'))
            result = getattr(records, 'add_' + args.command)(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
