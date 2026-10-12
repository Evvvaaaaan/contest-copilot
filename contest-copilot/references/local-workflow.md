# Local Application Workflow Protocol

Use this reference with the local browser application and its Codex CLI controller. User-facing messages and the interface are Korean; instructions, code, and structured field names are English. Read the phase-specific references for research, idea assessment, simulation design, and validation quality. This protocol connects those instructions to executable local components.

## 1. Runtime and Ownership

The application requires Python 3.9+ on macOS/Linux and an installed, authenticated Codex CLI. Start it from the repository root:

```sh
codex login
python3 web/server.py --port 8765
```

The browser opens at `http://127.0.0.1:8765`. `--no-open`, `--data-dir PATH`, and `--port PORT` support headless startup and isolated workspaces. Existing Codex authentication can be used without a separate LLM API key. Model inference is not offline; subscription, tool, network, and usage limits still apply. Other models and agent applications can use the portable skill manually, but the browser transport only integrates Codex CLI.

The controller owns acceptance state and execution scheduling. Chat supplies research and proposals. Development changes product files and executes checks. A fresh reviewer process inspects the snapshot and returns findings. Never let an ordinary chat response grant itself a pass, authenticate consent, or change the approved contract silently.

The controller uses separate fresh Codex execution contexts for development and review. Development uses workspace-write access; review uses read-only access. Separate contexts are not separate model families or proof of statistical independence. Checks requiring unavailable permissions, dependencies, or write access remain unverified. The host records role outputs and actual execution evidence; fluent explanations are insufficient.

Only run one mutating workflow per project. Save checkpoint and limit usage at meaningful boundaries. After interruption or restart, inspect persisted state and file freshness before resuming; do not silently reset budgets or assume a lost process finished.

## 2. Research and User Provenance

Read [research.md](research.md) and [idea-evaluation.md](idea-evaluation.md). Apply this priority order: official mandatory requirements, published judging criteria and weights, past winners and published judging comments, then supporting domestic/international evidence. Winning characteristics are not proven causes of winning.

Maintain a research map and a search log covering queries, languages, dates, primary materials inspected, unresolved gaps, contradictions, and useful new evidence. Use bounded search passes. Record why additional searches stopped: important coverage achieved, diminishing new evidence, explicit remaining uncertainty, or the agreed limit. Never claim to have searched all web information or invent a research completion percentage.

Use `project_records.py` to keep `records.json`:

| Collection | Core fields and rules |
|---|---|
| `sources` | `title`, `url` or relative `path`, `status: discovered|inspected`; inspected sources require `locator`, `accessed_at`, `excerpt`. Local files receive `sha256`. |
| `claims` | `text`, `kind: fact|interpretation|prediction`, `uncertainty`, `source_ids`. Facts require inspected sources; source revisions are captured. |
| `decisions` | `actor: user|assistant`, `original`, `revised`, `reason`, `message_ref`. A supplied record does not authenticate approval. |
| `documents` | Relative path, file hash, extraction backend, per-page or logical-section text/status, coverage, and limitations. |

New source/claim/decision records receive an ID; omit `id` when creating. Updates supply the existing ID and preserve revisions in `history`. Do not attribute an AI suggestion to the user. Record the user's original intent separately from the AI's proposal and the final choice.

Examples from the repository root, using actual project paths:

```sh
python3 contest-copilot/scripts/project_records.py --workspace /project source --input /project/source-input.json
python3 contest-copilot/scripts/project_records.py --workspace /project claim --input /project/claim-input.json
python3 contest-copilot/scripts/project_records.py --workspace /project decision --input /project/decision-input.json
python3 contest-copilot/scripts/project_records.py --workspace /project extract --file uploads/brief.pdf
python3 contest-copilot/scripts/project_records.py --workspace /project show
```

Text extraction supports text formats, HTML, DOCX main-document text, and optional PDF backends (`pypdf` or `pdftotext`). Missing backends, scanned pages, unreadable pages, omitted images, and unknown pagination are recorded explicitly. There is no built-in optical character recognition. Extraction is not confirmation that the complete document or its visual content was understood.

## 3. Propose the Contract and Limits

Write `workflow-proposal.json` in the project workspace. The controller presents it for initial confirmation. Example values are illustrative, not universally appropriate thresholds:

```json
{
  "contract": {
    "project": "Competition project name",
    "intent": "The user's core intended outcome",
    "max_iterations": 3,
    "conditions": [{
      "id": "core-flow",
      "source": "Official requirement or actual user decision reference",
      "required": true,
      "requirement": "Observable required behavior",
      "method": "Actual flow or measurement to execute",
      "target": "Evidence-based pass condition",
      "applicability": "Version, environment and scenario"
    }]
  },
  "limits": {"max_turns": 6, "max_seconds": 1800, "stagnation_rounds": 2}
}
```

`max_iterations` bounds review rounds. Controller limits additionally bound LLM turns, elapsed work, and consecutive rounds without sufficient progress. Confirm project-appropriate values once. Revisions to the purpose, required criteria, or budget require the user's actual decision; a routine failed check does not.

The controller starts development, freezes the artifact snapshot, starts a separate reviewer, records per-condition findings, and checks whether required conditions pass. If not, it continues from the findings within the agreed limits. Stop for user feedback after current required passes, or report incomplete on limits, stagnation, blocked prerequisites, or a necessary user decision.

Role outputs follow strict JSON contracts:

```json
{
  "outcome": "ready_for_review",
  "summary": "Korean summary of actual changes and checks",
  "question": "",
  "artifacts": ["src/main.py", "tests/test_core.py"]
}
```

The developer can instead return `needs_user` or `blocked`, with the actual missing decision or prerequisite. List every relevant source, test, configuration, and dependency file individually. Do not include mutable progress metadata or generated review evidence as the product snapshot.

```json
{
  "summary": "Korean review findings",
  "verdicts": [{
    "condition_id": "core-flow",
    "verdict": "unverified",
    "method": "The actual command or inspection attempted",
    "note": "Observed result and limitations",
    "evidence": [],
    "checks": []
  }]
}
```

The reviewer returns each condition exactly once. Verdicts are `pass`, `fail`, or `unverified`; evidence paths refer to existing workspace files. Each passing condition needs a nonempty `checks` array, for example `[{"command": "python3 -m unittest discover -s tests", "expected_exit_code": 0}]`. Use exact executed command text, including a `cd` prefix when supplied to the execution tool. The controller matches the command or its shell wrapper's command text against captured events and requires the latest matching execution to exit zero. An unrelated successful command does not satisfy a listed failed check.

For tests where a program is expected to fail, run an assertion wrapper that checks that expected failure and itself exits zero on success. The reviewer cannot redefine a failed check as passing by supplying a nonzero `expected_exit_code`. Existing evidence paths and required fields are validated before verdict mutation; host-written changes update the expected progress hash so an ordinary recording error is not mistaken for outside tampering.

Execution matching proves that the listed command ran with the recorded exit status. It does not prove the command substantively covers the condition, that a qualitative judgment is correct, or that the checks cannot be misleading. The reviewer must still establish relevance and interpret actual outputs against the approved target.

The controller manages `progress.json` through the state helper. In this application, chat and development roles must not invoke `init`, `contract`, `start`, or `record` to create their own success state. Standalone use outside the controller can follow [the state CLI reference](validation-loop.md#9-local-state-tool), with its explicit trust limitations.

Show actual preview URLs and current work as soon as available. Progress display does not require approval of each step. Feedback within the agreed scope belongs in the next development pass; never edit an artifact concurrently with its review.

## 4. Propose and Execute a Synthetic Experiment

Write `simulation-plan.json` with a configuration accepted by `Simulation.create`. The user reviews the configuration in the interface before the host starts bounded actor turns:

```json
{
  "candidate_id": "candidate-a",
  "candidate_version": "v1",
  "question": "Which adoption barriers appear in this scenario?",
  "max_rounds": 2,
  "baseline": {"scenario": "State the shared public conditions"},
  "participants": [{
    "id": "participant-1",
    "role": "Prospective user",
    "goals": ["State a relevant goal"],
    "constraints": ["State an applicable constraint"],
    "knowledge": ["State what this actor initially knows"],
    "resources": {"time": 2},
    "basis": ["Source IDs or explicitly labeled scenario assumptions"]
  }],
  "action_costs": {"try": {"time": 1}}
}
```

The engine persists `simulations/<run-id>/run.json`. Its Python API is `Simulation(workspace)` with `create`, `read`, `observation`, `apply`, `advance`, `stop`, and `summary`. The host gives the active actor only its observation and permitted actions. Responses have `event_id`, `actor_id`, `type`, and `reason`; `ask`/`share` also require `target_id` and `content`. Valid action types are `try`, `adopt`, `reject`, `ask`, `share`, and `wait`.

Each actor acts once per round, with resources and allowed transitions checked before mutation. Adoption requires an earlier trial. Duplicate event IDs with the same action are idempotent; conflicting duplicates are rejected. Advance only when the current round is complete. Execution is bounded by the approved round count and the application's simulation timeout. The browser stops and preserves the run on failure or interruption; it does not automatically resume stopped simulations. Inspect saved events and configuration before deciding to create another run. The standalone API can incrementally operate on a still-running saved experiment.

The browser actor response schema uses `type`, `reason`, `target_id`, and `content`; unused message fields are empty. The host supplies event/actor IDs and removes unused fields before calling `apply`. Actor calls must not use tools or read files; the host checks captured events and rejects detected tool use. Limited prompt observations are not a guarantee of perfect model knowledge isolation.

The baseline hash captures participants, baseline conditions, round count, and scheduling rules. Candidate identity, question, and action costs remain separately recorded: matching baseline hashes alone do not prove a fair comparison. Examine those differences and start candidates with reset participant memories.

Every trial, message, adoption, and rejection is synthetic. A simulated trial does not exercise the real product. Counts describe this experiment only, not market demand, real adoption probability, forecast accuracy, or independent human observations. Use real evidence and actual product checks separately.

## 5. Accept the Result and Prepare Submission Files

After required conditions pass, show the result and wait for acceptance or changes. A review pass is not user acceptance. A new user message after workflow approval marks a pending revision and blocks finalization until that feedback has been addressed. Continue through the interface's resume action to run a new development/review pass under the same approved conditions. If the feedback changes criteria or budgets, propose a revised agreement instead. Resume preserves consumed turns, elapsed time, and review counts; it does not provide a fresh allowance. Stale artifact/evidence hashes invalidate old passes even if no feedback message was sent.

Prepare `submission-spec.json` using the `example` object in [the bundled specification](../assets/submission-spec.json). The file's outer schema wrapper is not itself a build specification. Required build fields are:

| Field | Meaning |
|---|---|
| `project`, `title` | Accepted contract project name and report title |
| `official_instructions` | Objects with `id`, `text`, optional `source_id`, and `condition_ids` mapping the instruction to passing conditions |
| `accepted` | `artifact_version`, `contract_version`, `iteration`, `decision_reference`; the web host injects the actual accepted snapshot and decision |
| `sections` | Section `title` and `claims` with `kind`, `text`, optional `source_ids`, and `evidence` objects containing relative `path` and `sha256` |
| `formats` | Objects with `format`, safe `filename`, and optional `max_bytes` or page constraints |
| `source_files` | Explicit relative files for a requested source ZIP |
| `user_decision_ids` | Existing user-authored decision records to include |

Submission claim kinds are `implemented`, `measured`, `simulated`, and `planned`. This differs from the research claim classification. All except planned claims require actual evidence files. Do not copy predictions into measured results. Do not invent the `accepted` block to bypass a pending user decision.

`build_submission.build(workspace, spec)` and its CLI produce only selected Markdown (`md`), HTML (`html`), and ZIP (`zip`) files under `submission/`, plus `manifest.json`:

HTML reports use semantic headings, paragraphs, and labeled lists. Sources and user decisions are presented as readable fields with their record IDs and references. User-supplied text is escaped, not interpreted as HTML or arbitrary Markdown. The Markdown output retains its own heading and list syntax.

```sh
python3 contest-copilot/scripts/build_submission.py --workspace /project --spec /project/submission-spec.json
```

The builder checks current required passes, accepted versions, evidence/source hashes, referenced records, official requirement mappings, safe paths, output sizes, and file readback. Unsupported formats including PDF, DOCX, and PPTX, unverified page counts, unmapped official requirements, and size violations prevent ready status. Previously generated outputs edited by the user are preserved rather than overwritten.

`ready_for_local_review` means the builder's checks passed. It is not proof of visual quality, factual correctness, user consent authenticity, or official compliance beyond the recorded checks. The manifest reports whether visual rendering was performed and contains output hashes and input snapshots for freshness checks. Open/render the actual files before claiming presentation quality. External submission remains false; sending files to an organizer requires separate authorization and receipt evidence.
