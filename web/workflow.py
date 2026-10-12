"""Bounded local orchestration. Every role gets a fresh Codex context."""
import hashlib
import json
import os
import shlex
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

SCRIPTS = Path(__file__).resolve().parents[1] / 'contest-copilot' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from project_records import Records
from simulate import Simulation
from build_submission import build
import manage_state


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    os.replace(temporary, path)


def envelope(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


STRING = {'type': 'string'}
STRINGS = {'type': 'array', 'items': STRING}
DEVELOPER = envelope({'outcome': {'type': 'string', 'enum': ['ready_for_review', 'needs_user', 'blocked']},
                      'summary': STRING, 'question': STRING, 'artifacts': STRINGS})
REVIEWER = envelope({'summary': STRING, 'verdicts': {'type': 'array', 'items': envelope({
    'condition_id': STRING, 'verdict': {'type': 'string', 'enum': ['pass', 'fail', 'unverified']},
    'method': STRING, 'note': STRING, 'evidence': STRINGS, 'checks': {'type': 'array', 'items': envelope({'command': STRING, 'expected_exit_code': {'type': 'integer', 'enum': [0]}})}})}})
ACTION = envelope({'type': {'type': 'string', 'enum': ['try', 'adopt', 'reject', 'ask', 'share', 'wait']},
                   'reason': STRING, 'target_id': STRING, 'content': STRING})


class Controller:
    def __init__(self, app, project_id):
        self.app, self.id = app, project_id
        self.directory = app.directory(project_id)
        self.workspace = self.directory / 'workspace'
        self.path = self.directory / 'workflow.json'

    def load(self):
        return json.loads(self.path.read_text()) if self.path.exists() else None

    def proposal(self, name):
        path = self.workspace / name
        if not path.exists():
            return None
        if path.is_symlink():
            raise ValueError('설정 파일은 심볼릭 링크일 수 없습니다.')
        return {'hash': digest(path), 'value': json.loads(path.read_text())}

    def checked_proposal(self, name, expected):
        proposal = self.proposal(name)
        if not proposal or proposal['hash'] != expected:
            raise ValueError('설정이 변경됐습니다. 새로 표시된 내용을 확인해 주세요.')
        return proposal

    def state_command(self, *arguments):
        args = manage_state.parser().parse_args(['--state', str(self.workspace / 'progress.json'), *arguments])
        # All web mutations are serialized by one job per project.
        return manage_state.execute(args, self.workspace / 'progress.json')

    def approval(self, message):
        entry = self.app.append_message(self.id, 'user', message)
        Records(self.workspace).add_decision({'actor': 'user', 'original': message, 'revised': message,
                                             'reason': 'Explicit action in the local application.',
                                             'message_ref': entry['id']})
        return entry['id']

    def approve(self, expected):
        proposal = self.checked_proposal('workflow-proposal.json', expected)
        value = proposal['value']
        manage_state.validate_contract(value['contract'])
        limits = value['limits']
        for key in ('max_turns', 'max_seconds', 'stagnation_rounds'):
            if type(limits.get(key)) is not int or limits[key] <= 0:
                raise ValueError(key + ' must be a positive integer')
        if limits['max_turns'] < 2:
            raise ValueError('개발과 검토에 최소 2회 실행이 필요합니다.')
        old = self.load()
        if old and old['proposal_hash'] == expected:
            raise ValueError('이미 승인한 조건입니다. 이어가기를 사용해 주세요.')
        decision = self.approval('표시된 목표 조건과 실행 한도를 승인하고 자동 진행합니다.')
        contract_path = self.directory / 'approved-contract.json'
        write(contract_path, value['contract'])
        progress_path = self.workspace / 'progress.json'
        if progress_path.exists():
            self.state_command('contract', '--contract', str(contract_path), '--decision', decision)
        else:
            self.state_command('init', '--project-root', str(self.workspace), '--contract', str(contract_path), '--decision', decision)
        workflow = {'pending_artifacts': None, 'proposal_hash': expected, 'contract': value['contract'], 'limits': limits,
                    'decision_reference': decision, 'status': 'running', 'role': None, 'turns': 0,
                    'elapsed_seconds': 0, 'round': 0, 'stagnation': 0, 'last_signature': None,
                    'findings': None, 'reason': '', 'runs': [], 'progress_hash': digest(progress_path)}
        write(self.path, workflow)
        return workflow

    def start(self, action, body):
        with self.app.lock:
            if self.id in self.app.jobs:
                raise ValueError('진행 중인 작업을 먼저 중단해 주세요.')
            if not self.app.codex and action != 'finalize':
                raise ValueError('Codex 연결이 필요합니다.')
            if action == 'finalize':
                return self.finalize(body.get('hash'))
            if action == 'approve':
                self.approve(body.get('hash'))
            elif action == 'resume':
                workflow = self.load()
                if not workflow or workflow['status'] not in ('interrupted', 'needs_user', 'failed'):
                    raise ValueError('이어서 실행할 작업이 없습니다.')
                self.check_progress(workflow)
                workflow.update(status='running', reason='')
                write(self.path, workflow)
            elif action == 'simulate':
                proposal = self.checked_proposal('simulation-plan.json', body.get('hash'))
                config = proposal['value']
                # Engine validates config first, before logging an approval.
                run = Simulation(self.workspace).create(config)
                self.approval('표시된 가상 참여자와 반복 횟수로 영향 시뮬레이션 실행을 승인합니다.')
                write(self.directory / 'simulation-job.json', {'run_id': run['run_id'], 'status': 'running'})
            else:
                raise ValueError('알 수 없는 작업입니다.')
            job = {'id': uuid.uuid4().hex, 'process': None, 'stop': threading.Event(), 'timeout': False}
            self.app.jobs[self.id] = job
            self.app.update(self.id, status='running', activity='자동 작업을 시작합니다.')
            target = self.simulate if action == 'simulate' else self.run
            threading.Thread(target=target, args=(job,), daemon=True).start()
            return {'accepted': True}

    def check_progress(self, workflow):
        state = json.loads((self.workspace / 'progress.json').read_text())
        if digest(self.workspace / 'progress.json') != workflow['progress_hash']:
            raise ValueError('검증 상태가 자동 실행기 밖에서 변경됐습니다. 조건을 다시 확인해 주세요.')
        if state['contract'] != workflow['contract']:
            raise ValueError('승인한 조건과 진행 기록이 다릅니다. 조건을 다시 확인해 주세요.')
        return state

    def turn(self, role, prompt, schema, job, timeout):
        if job['stop'].is_set():
            raise InterruptedError('사용자가 작업을 중단했습니다.')
        run_id = uuid.uuid4().hex
        directory = self.directory / 'runs' / run_id
        directory.mkdir(parents=True)
        write(directory / 'schema.json', schema)
        sandbox = 'workspace-write' if role == 'developer' else 'read-only'
        command = [self.app.codex, '--search', '-c', f'sandbox_mode="{sandbox}"', '-c', 'approval_policy="never"',
                   'exec', '--json', '--skip-git-repo-check', '--output-schema', str(directory / 'schema.json'), '-']
        working_directory = self.workspace
        if role == 'participant':
            working_directory = directory / 'isolated'
            working_directory.mkdir()
            command.remove('--search')
            command[command.index('exec') + 1:command.index('exec') + 1] = ['--ignore-user-config', '--ignore-rules', '--ephemeral']
            for setting in ('web_search="disabled"', 'project_doc_max_bytes=0',
                            'features.shell_tool=false', 'features.apps=false', 'features.plugins=false',
                            'features.multi_agent=false', 'features.view_image=false',
                            'features.browser_use=false', 'features.computer_use=false', 'features.image_generation=false', 'features.hooks=false'):
                command[1:1] = ['-c', setting]
        completed, final, error, events = False, None, None, []
        process = None
        timer = None
        self.app.update(self.id, activity={'developer': '개발 담당이 결과물을 개선하고 있습니다.',
                                          'reviewer': '별도 검토 담당이 조건을 확인하고 있습니다.',
                                          'participant': '가상 참여자의 행동을 실행하고 있습니다.'}[role])
        try:
            with (directory / 'stderr.log').open('w') as errors:
                process = subprocess.Popen(command, cwd=working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=errors, text=True, encoding='utf-8', start_new_session=True)
                with self.app.lock:
                    job['process'] = process
                    if job['stop'].is_set():
                        self.app.terminate(process)
                def expire():
                    job['timeout'] = True
                    job['stop'].set()
                    self.app.terminate(process)
                timer = threading.Timer(max(0.01, timeout), expire)
                timer.daemon = True
                timer.start()
                process.stdin.write(prompt)
                process.stdin.close()
                for line in process.stdout:
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get('type') == 'turn.completed':
                        completed = True
                    if event.get('type') in ('error', 'turn.failed'):
                        error = event.get('error', event.get('message', 'Agent failed'))
                    item = event.get('item', {})
                    if event.get('type') == 'item.completed' and item.get('type') in ('command_execution', 'web_search', 'file_change', 'mcp_tool_call'):
                        events.append(event)
                    if item.get('type') == 'agent_message' and item.get('text'):
                        final = item['text']
                code = process.wait(timeout=5)
                if job['stop'].is_set():
                    raise InterruptedError('실행 시간 한도에 도달했습니다.' if job['timeout'] else '사용자가 작업을 중단했습니다.')
                if code or error or not completed:
                    raise ValueError(str(error or (directory / 'stderr.log').read_text()[-1500:] or 'Agent did not complete'))
                result = json.loads(final or '{}')
                if set(result) != set(schema['required']):
                    raise ValueError('에이전트 응답에 필수 항목이 없습니다.')
                write(directory / 'result.json', result)
                return result, {'run_id': run_id, 'role': role, 'events': events, 'result': result,
                                'context': 'fresh', 'sandbox': sandbox}
        finally:
            write(directory / 'events.json', events)
            if timer:
                timer.cancel()
            if process:
                if process.poll() is None or job['stop'].is_set():
                    self.app.terminate(process)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, 9)
                    process.wait()
                process.stdout.close()
            job['process'] = None

    def run(self, job):
        workflow = self.load()
        started = time.monotonic()
        prior_elapsed = workflow['elapsed_seconds']
        def persist():
            workflow['elapsed_seconds'] = prior_elapsed + time.monotonic() - started
            workflow['saved_at_epoch'] = time.time()
            write(self.path, workflow)
        def agent(role, prompt, schema):
            persist()
            limits = workflow['limits']
            remaining = limits['max_seconds'] - workflow['elapsed_seconds']
            if workflow['turns'] >= limits['max_turns'] or remaining <= 0:
                raise TimeoutError('합의한 실행 횟수 또는 시간 한도에 도달했습니다.')
            workflow['turns'] += 1
            workflow['role'] = role
            persist()
            result, log = self.turn(role, prompt, schema, job, min(self.app.timeout, remaining))
            workflow['runs'].append({'run_id': log['run_id'], 'role': role})
            persist()
            return result, log
        try:
            while True:
                if job['stop'].is_set():
                    raise InterruptedError('사용자가 작업을 중단했습니다.')
                state = self.check_progress(workflow)
                progress = manage_state.report(state)
                if progress['status'] == 'ready_for_user_review' and not workflow.get('revision_requested'):
                    workflow.update(status='ready_for_user_review', reason='필수 조건 검증을 통과했습니다. 사용자 확인을 기다립니다.')
                    break
                if not workflow.get('pending_artifacts') and (workflow['round'] >= workflow['contract']['max_iterations'] or progress['status'] == 'limit_reached'):
                    raise TimeoutError('합의한 검토 반복 한도에 도달했습니다.')
                if not workflow.get('pending_artifacts'):
                    before = digest(self.workspace / 'progress.json')
                    messages = self.app.load(self.id)['messages']
                    prompt = f'''You are the implementation agent for a local competition project. Respond structured JSON, summaries in Korean.
    Read {SCRIPTS.parent / 'SKILL.md'} and relevant references. Work only in this workspace.
    Implement/refine the project against the immutable contract below. Run meaningful checks. Do not change progress.json, records approvals, or application metadata. Do not publish anything.
    Return ready_for_review only when artifact paths list ALL relevant source, test, specification and dependency files (individual relative files, not directories). Never report a verdict for your own work. Return needs_user for a genuine missing decision. Preserve user changes.
    Contract: {json.dumps(workflow['contract'], ensure_ascii=False)}
    User conversation: {json.dumps(messages, ensure_ascii=False)}
    Previous review findings: {json.dumps(workflow['findings'], ensure_ascii=False)}'''
                    draft, _ = agent('developer', prompt, DEVELOPER)
                    if digest(self.workspace / 'progress.json') != before:
                        raise ValueError('개발 담당이 검증 상태를 변경했습니다. 자동 진행을 중단했습니다.')
                    if draft['outcome'] != 'ready_for_review':
                        workflow.update(status='needs_user', reason=draft['summary'] + '\n' + draft['question'])
                        break
                    artifacts = draft['artifacts']
                    if not artifacts or not all(isinstance(p, str) and not Path(p).is_absolute() for p in artifacts):
                        raise ValueError('개발 담당이 검토할 파일 목록을 제공하지 않았습니다.')
                    paths = [self.app.file(self.id, p) for p in artifacts]
                    if self.workspace / 'progress.json' in paths or any(p.parts[len(self.workspace.parts)] in ('evidence', 'submission') for p in paths):
                        raise ValueError('검증 상태나 생성 보고서를 개발 결과물로 사용할 수 없습니다.')
                    workflow['round'] += 1
                    args = ['start', '--version', f'auto-{workflow["round"]}-{uuid.uuid4().hex[:8]}']
                    for path in paths:
                        args += ['--artifact', str(path)]
                    self.state_command(*args)
                    workflow['progress_hash'] = digest(self.workspace / 'progress.json')
                    workflow['pending_artifacts'] = artifacts
                    workflow['revision_requested'] = False
                    persist()
                    before = digest(self.workspace / 'progress.json')
                else:
                    artifacts = workflow['pending_artifacts']
                    if not manage_state.unchanged(state['iterations'][-1]['artifacts']):
                        workflow['pending_artifacts'] = None
                        persist()
                        continue
                before = digest(self.workspace / 'progress.json')
                prompt = f'''You are a separate reviewer with no developer conversation. Review the actual frozen files, not implementation claims.
Respond structured JSON with Korean observations. Read-only workspace; run real checks with PYTHONDONTWRITEBYTECODE=1 where appropriate, use /tmp for transient test files. Never modify project files or progress.json. Do not publish.
For EVERY condition, provide pass/fail/unverified, actual method and observed result, and existing relative evidence paths (may be empty; host captures your actual tool output). For each condition provide checks: a list of actual shell commands you ran (exact command text supplied to the tool, including any cd prefix) and expected_exit_code (normally 0). Inspection checks can cat/read relevant files with a command. The host matches these against captured execution events. A pass requires at least one matching check; do not reference unexecuted commands. Pass only with actual inspected or executed evidence; unavailable tools or unproven claims are unverified. Simulation is never real user validation.
Contract: {json.dumps(workflow['contract'], ensure_ascii=False)}
Frozen artifact files: {json.dumps(artifacts)}'''
                review, log = agent('reviewer', prompt, REVIEWER)
                if digest(self.workspace / 'progress.json') != before:
                    raise ValueError('검토 담당이 검증 상태를 변경했습니다.')
                current = self.check_progress(workflow)
                if not manage_state.unchanged(current['iterations'][-1]['artifacts']):
                    raise ValueError('검토 중 결과물이 변경됐습니다. 다시 검증해야 합니다.')
                evidence_dir = self.workspace / 'evidence'
                if evidence_dir.is_symlink():
                    raise ValueError('근거 폴더는 심볼릭 링크일 수 없습니다.')
                evidence_dir.mkdir(exist_ok=True)
                evidence = evidence_dir / (log['run_id'] + '.json')
                write(evidence, log)
                judgments = review['verdicts']
                ids = [v['condition_id'] for v in judgments]
                expected = [c['id'] for c in workflow['contract']['conditions']]
                if len(ids) != len(set(ids)) or set(ids) != set(expected):
                    raise ValueError('검토 결과가 합의한 조건 목록과 다릅니다.')
                for verdict in judgments:
                    if not isinstance(verdict.get('method'), str) or not verdict['method'].strip() or not isinstance(verdict.get('note'), str) or not verdict['note'].strip():
                        raise ValueError('검토 방법과 실제 관찰 내용이 필요합니다.')
                    for relative in verdict['evidence']:
                        self.app.file(self.id, relative)
                for verdict in judgments:
                    if verdict['verdict'] not in ('pass', 'fail', 'unverified'):
                        raise ValueError('잘못된 검토 판정입니다.')
                    checks = verdict.get('checks', [])
                    usable = bool(checks)
                    for check in checks:
                        matches = []
                        for event in log['events']:
                            item = event.get('item', {})
                            if item.get('type') != 'command_execution':
                                continue
                            command = item.get('command', '')
                            try:
                                parts = shlex.split(command)
                                canonical = parts[-1] if len(parts) >= 3 and parts[-2] in ('-lc', '-c') else command
                            except ValueError:
                                canonical = command
                            if check.get('command', '').strip() in (command.strip(), canonical.strip()):
                                matches.append(item)
                        if not matches or type(check.get('expected_exit_code')) is not int or check['expected_exit_code'] != 0 or matches[-1].get('exit_code') != 0:
                            usable = False
                    if verdict['verdict'] == 'pass' and not usable:
                        verdict.update(verdict='unverified', note='조건에 연결된 실제 명령과 예상 종료 결과가 확인되지 않았습니다. ' + verdict['note'])
                    args = ['record', '--condition', verdict['condition_id'], '--verdict', verdict['verdict'],
                            '--method', verdict['method'], '--note', verdict['note'], '--review-mode', 'separate_context',
                            '--evidence', str(evidence)]
                    for relative in verdict['evidence']:
                        args += ['--evidence', str(self.app.file(self.id, relative))]
                    self.state_command(*args)
                    workflow['progress_hash'] = digest(self.workspace / 'progress.json')
                    persist()
                workflow['progress_hash'] = digest(self.workspace / 'progress.json')
                workflow['pending_artifacts'] = None
                workflow['findings'] = review
                progress = self.state_command('status')
                signature = json.dumps([(c['id'], c['verdict']) for c in progress['conditions']])
                workflow['stagnation'] = workflow['stagnation'] + 1 if signature == workflow['last_signature'] else 0
                workflow['last_signature'] = signature
                persist()
                if progress['status'] != 'ready_for_user_review' and workflow['stagnation'] >= workflow['limits']['stagnation_rounds']:
                    workflow.update(status='stalled', reason='반복 검토에서 조건 충족 상태가 개선되지 않았습니다.')
                    break
        except InterruptedError as error:
            workflow.update(status='limit_reached' if job['timeout'] else 'interrupted', reason=str(error))
        except TimeoutError as error:
            workflow.update(status='limit_reached', reason=str(error))
        except Exception as error:
            workflow.update(status='failed', reason=str(error))
        finally:
            workflow['role'] = None
            persist()
            self.finish(job, workflow['reason'], workflow['status'])

    def finish(self, job, message, status):
        self.app.append_message(self.id, 'assistant', message)
        with self.app.lock:
            self.app.update(self.id, status='failed' if status == 'failed' else 'interrupted' if status == 'interrupted' else 'idle', activity=message)
            self.app.jobs.pop(self.id, None)

    def simulate(self, job):
        path = self.directory / 'simulation-job.json'
        metadata = json.loads(path.read_text())
        engine = Simulation(self.workspace)
        run_id = metadata['run_id']
        started = time.monotonic()
        try:
            snapshot = engine.read(run_id)
            while snapshot['state']['status'] == 'running':
                for participant in snapshot['config']['participants']:
                    observation = engine.observation(run_id, participant['id'])
                    remaining = self.app.timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        raise TimeoutError('시뮬레이션 실행 시간 한도에 도달했습니다.')
                    prompt = f'''You represent ONE synthetic participant, not a real surveyed person. No tools, no file reads, no web search. Use only the isolated observation below. Choose one of the allowed actions, respecting resources and prior experience. Provide concise Korean reason. target_id/content are empty except for ask/share. Do not infer hidden knowledge or claim real market probabilities.
{json.dumps(observation, ensure_ascii=False)}'''
                    action, log = self.turn('participant', prompt, ACTION, job, remaining)
                    if log['events']:
                        raise ValueError('가상 참여자가 허용되지 않은 외부 자료에 접근했습니다.')
                    action.update(event_id=uuid.uuid4().hex, actor_id=participant['id'])
                    if action['type'] not in ('ask', 'share'):
                        action.pop('target_id', None)
                        action.pop('content', None)
                    engine.apply(run_id, action)
                snapshot = engine.advance(run_id)
            metadata.update(status='completed', summary=engine.summary(run_id))
            message = '가상 참여자 시뮬레이션을 마쳤습니다. 행동 기록과 제한 사항을 확인해 주세요. 실제 사용자 조사나 수상 확률이 아닙니다.'
        except Exception as error:
            engine.stop(run_id)
            metadata.update(status='interrupted' if job['stop'].is_set() else 'failed', error=str(error))
            message = '시뮬레이션이 중단됐습니다: ' + str(error)
        write(path, metadata)
        self.finish(job, message, metadata['status'])

    def finalize(self, expected):
        proposal = self.checked_proposal('submission-spec.json', expected)
        report = self.state_command('status')
        if report['status'] != 'ready_for_user_review':
            raise ValueError('현재 결과물의 필수 조건을 먼저 검증해 주세요.')
        workflow = self.load()
        if not workflow:
            raise ValueError('승인된 자동 검증 기록이 필요합니다.')
        if workflow.get('revision_requested'):
            raise ValueError('추가 의견을 반영한 검증을 먼저 진행해 주세요.')
        state = self.check_progress(workflow)
        decision = self.approval('현재 통과한 결과물과 표시된 출력 설정을 확인하고 제출물 생성을 승인합니다.')
        spec = proposal['value']
        spec['accepted'] = {'artifact_version': state['iterations'][-1]['artifact_version'],
                            'contract_version': state['contract_version'], 'iteration': len(state['iterations']),
                            'decision_reference': decision}
        manifest = build(self.workspace, spec)
        self.app.append_message(self.id, 'assistant', '제출물을 생성했습니다. ' + ('로컬 검사를 통과했습니다. 최종 내용을 확인해 주세요.' if manifest['status'] == 'ready_for_local_review' else '충족하지 못한 출력 조건이 있습니다. 제출물 검증 내용을 확인해 주세요.'))
        self.app.update(self.id, activity='제출물 생성 결과를 확인해 주세요.')
        return manifest
