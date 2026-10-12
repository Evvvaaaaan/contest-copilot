<div align="center">

# Contest Copilot

**Turn competition briefs and your ideas into evidence-backed projects.**

A local web workspace, reusable AI instructions, and Python tools for researching competitions, developing ideas, running stakeholder experiments, and preparing evidence-linked submissions.

[![Checks](https://github.com/Evvvaaaaan/contest-copilot/actions/workflows/checks.yml/badge.svg)](https://github.com/Evvvaaaaan/contest-copilot/actions/workflows/checks.yml)
![Status: Early development](https://img.shields.io/badge/status-early_development-orange)
![Python: 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
[![GitHub stars](https://img.shields.io/github/stars/Evvvaaaaan/contest-copilot?style=social)](https://github.com/Evvvaaaaan/contest-copilot/stargazers)

[Get started](#get-started) · [What works today](#what-works-today) · [Workflow](#workflow) · [Roadmap](#roadmap)

</div>

## Why Contest Copilot?

Competition preparation involves more than generating an idea. You need to understand the judging criteria, investigate previous winners, preserve your own perspective, build something feasible, and support the final claims with evidence.

Contest Copilot gives an AI assistant a structured procedure for that work. First, agree on the project goal, the checks needed to accept the result, and how long the assistant may keep working. The assistant then develops and reviews the work within those limits and presents the result when the required checks pass.

**This project combines a local browser app connected to Codex with explicit requirements, separate development and review, research records, synthetic stakeholder experiments, and submission packaging.** The core Python tools use the standard library. The application coordinates model calls through your installed Codex CLI.

## What works today

| Capability | Current status |
|---|---|
| Competition research | Search procedure plus versioned sources, claims, and document extraction records |
| User intent and idea assessment | Original/revised decisions with author and conversation references |
| Stakeholder experiments | Persistent actors, resources, limited observations, actions, rounds, stop, and summaries |
| Development and review | Controller protocol for fresh development and read-only review contexts with explicit limits |
| Acceptance checks | Per-condition verdicts, artifact/evidence hashes, and stale-result detection |
| Browser workspace | Codex conversation, uploads, progress, feedback, and downloadable files |
| Submission files | Markdown, HTML, source ZIP, and verification manifests |
| PDF, DOCX, PPTX generation | Unsupported; required unsupported formats remain incomplete |
| Real competition outcome | No demonstrated award result or validated real-world adoption forecast |

The state helper does not call an LLM API. The local web app invokes your installed Codex CLI and can use its existing ChatGPT login without an additional API key. Your assistant supplies reasoning and executes checks; the helper stores results and checks whether recorded files have changed. AI requests still go to the configured provider: local storage does not mean offline inference. Subscription, tool availability, and usage limits still apply.

## Workflow

1. **Research the competition.** Read the announcement, amendments, eligibility rules, judging criteria, previous winners, and domestic and international evidence. Follow primary sources and record gaps and contradictions.
2. **Understand your idea.** Hear your problem framing and experience before proposing concrete solutions. Preserve your intended outcome while considering better ways to achieve it.
3. **Agree on project requirements and working limits.** Define the required results, checks, targets, evidence, and maximum review rounds. Follow the official competition requirements before drawing conclusions from previous winners.
4. **Run bounded stakeholder experiments.** Review the configuration, then compare shortlisted ideas through relevant usage, adoption, and information-exchange scenarios. Actors receive limited observations; local code validates actions and saves each state change.
5. **Iterate through planning, development, and review.** Build the smallest useful core flow. Review actual evidence, address failures, and repeat within the agreed limits. Make a running frontend available for feedback when the host and project support it.
6. **Report and collect feedback.** Report after required conditions pass, or report incomplete status when blocked or limited. Incorporate feedback without silently changing the user's purpose.
7. **Prepare the required submission.** Match claims and deliverables to the accepted implementation, measured results, and official format. External submission requires authorization.

Simulated reactions are not real user research. A successful CLI invocation is not a passing product test. An LLM's self-assigned score is not evidence that a requirement has been met.

Research prioritizes official rules and published judging criteria, then past winners and judging comments, followed by domestic and international supporting evidence. The assistant records queries, inspected sources, coverage gaps, contradictions, and the reason it stopped searching. It does not promise to find every web page. Source records preserve what was supplied; they do not independently prove a claim true.

## Get started

### 1. Download the repository

```sh
git clone https://github.com/Evvvaaaaan/contest-copilot.git
cd contest-copilot
```

### 2. Open the local web app

Install Python 3.9+ and the [Codex CLI](https://developers.openai.com/codex/cli/) on macOS or Linux, then sign in to Codex once:

```sh
codex login
python3 web/server.py --port 8765
```

The app opens `http://127.0.0.1:8765` in your browser. Create a project, attach a competition brief or paste its URL, and send your message. Conversations, files, and progress are saved locally. Subsequent messages resume the project's Codex thread.

- See actual AI messages, current activity, saved stages, verification conditions, and downloadable files.
- Stop a running task, or use **Stop and send** to interrupt it and send revised instructions. This starts a new turn in the same conversation; it does not inject text into an in-flight turn.
- Upload source documents up to 10 MB each. Extraction depends on tools available to Codex; uploading a PDF does not guarantee that a PDF reader is installed.
- Initial progress comes from `ui-state.json`. After the user agrees to acceptance conditions, the app displays actual `manage_state.py` records. It does not fabricate a completion percentage.
- The assistant proposes `workflow-proposal.json`; confirm the initial conditions and limits once before automatic development/review. The host owns acceptance state, so a chat reply cannot approve its own result.
- After a workflow has been approved, sending feedback marks a pending revision and blocks finalization. Use the resume control to apply it under the same conditions and remaining limits. Changed criteria or a larger budget require a revised proposal.
- Review `simulation-plan.json` before running a synthetic experiment. Accept the reviewed product before building the proposed `submission-spec.json` package.
- The interface is Korean. Skill instructions and source code are English.

The first web connector supports **Codex CLI**. Other AI tools can use the skill instructions, but are not yet connected to the web chat.

Data is stored in `~/.local/share/contest-copilot/` by default. Use `--data-dir PATH` for a separate workspace and `--port 8766` if the default port is busy. Use `--no-open` to start without opening a browser. Test against a separate data directory and port; do not put sample conversations in a user's working projects.

The server listens only on the local loopback interface. Development uses a workspace-write sandbox and separate review uses a read-only sandbox. The app cannot request interactive command approvals; blocked commands must be reported. Each turn has a 30-minute default limit, configurable with `--turn-timeout SECONDS`. The approved workflow also has project-level turn, elapsed-time, review-round, and stagnation limits. Interrupted work must be resumed from its recorded state, not treated as finished.

### 3. Use the skill in another compatible agent

The installable skill folder is **`contest-copilot/`**, inside the repository. Register that folder using your agent's supported skill installation mechanism, or ask a file-capable agent to read its entrypoint:

```text
Read contest-copilot/SKILL.md and follow the relevant references.
Help me prepare for this competition: [announcement URL or file].
Begin with research. Preserve my ideas and record evidence.
Agree on acceptance criteria and execution limits before development.
```

Each AI application has its own installation steps and available tools. Downloading this repository does not automatically activate these instructions in every application.

### 4. Run the checks

With Python 3.9+ on macOS or Linux:

```sh
python3 contest-copilot/scripts/manage_state.py --help
python3 contest-copilot/scripts/project_records.py --help
python3 contest-copilot/scripts/simulate.py --help
python3 contest-copilot/scripts/build_submission.py --help
python3 -m unittest discover -s tests -v
```

No third-party Python packages are required for the web server or core commands. PDF extraction optionally uses `pypdf` or `pdftotext`; missing backends and unreadable pages are recorded. There is no built-in OCR. Text extraction does not verify diagrams, images, or complete rendered pagination.

Tests use temporary workspaces. Protocol fixtures do not prove model behavior, research depth, prediction accuracy, or competition quality. Run the tests in your environment and inspect actual output; this README does not assert that every host, model, or end-to-end competition process has been validated.

For the contract schema and command examples, read [Local State Tool](contest-copilot/references/validation-loop.md#9-local-state-tool).

For proposal schemas, ownership rules, records, simulation configuration, and submission formats, read [Local Workflow Protocol](contest-copilot/references/local-workflow.md).

## State management

| Command | Purpose |
|---|---|
| `init` | Save the initial agreed contract in a new project state file |
| `contract` | Record a revised contract and a reference to the user's decision |
| `start` | Begin a numbered review iteration and snapshot specified artifact files |
| `record` | Store a condition verdict, method, observations, and evidence files |
| `checkpoint` | Save the current phase, next action, notes, and optional preview URL |
| `status` | Recheck file hashes and derive the current acceptance status |
| `history` | Inspect earlier contracts, iterations, verdicts, and checkpoints |

The helper requires evidence files for a pass, rejects waivers of required conditions, and invalidates verdicts when registered artifacts or evidence files change. A new contract invalidates earlier acceptance without erasing history.

The web reviewer additionally links each condition to exact executed commands. Passing conditions require matching successful execution events; unrelated successful commands cannot make a listed failed check pass. This checks execution provenance, not whether the test design or reviewer judgment is substantively correct. Negative tests should use an assertion wrapper that exits zero when the expected failure occurs.

`ready_for_user_review` means all required conditions have recorded, current passes. It does not authenticate those judgments or mean the user has accepted the result. `limit_reached` means no new review iteration can start under the current allowance; the current review can still finish.

Only registered files are fingerprinted. Reviewers must separately check unlisted files, external services, runtime conditions, and whether the evidence actually proves the target. The standalone helper enforces review-round limits; the web controller coordinates its additional time, turn, and stagnation limits. In the web workflow, chat and development must not use this CLI to grant their own passes.

Keep competition-specific state, source materials, and evidence in a separate project directory. They are not part of this reusable skill.

## Evidence, simulation, and submission tools

| Component | Stored state or output | Responsibility |
|---|---|---|
| `project_records.py` | `records.json` | Versioned sources, cited claims, user/assistant decisions, document extraction coverage |
| `simulate.py` | `simulations/<run-id>/run.json` | Actor observations, allowed actions, resource changes, event history, bounded rounds |
| `build_submission.py` | `submission/` | Requested MD/HTML/ZIP files and an input/output hash manifest |

The simulation engine does not call a model itself. The host supplies an actor's decision, then the engine checks and applies it. `try` is a simulated trial, not a real product test. Actor histories and configuration differences should be inspected before comparing runs.

Open **영향 시뮬레이션 → 전체 대화·의견 보기** to inspect saved actions and reasons, messages with sender/recipient, and decision changes. All candidates/runs are shown together by default with full message text and action reasons. Optionally filter by candidate/run, participant, round, or conversations only; **전체 기록 보기** resets those filters. Download either one original run or all loaded run snapshots as JSON. The viewer reads existing `run.json` files; it never invents missing dialogue. Original records can be downloaded, and running experiments can be refreshed without restarting the model.

The browser retains interrupted simulation logs, but does not automatically restart a failed or stopped simulation. Inspect its saved state before deciding whether to run a new experiment. The development/review workflow has its own explicit resume controls and retains consumed limits.

Submission generation requires all current required checks to pass and a matching accepted artifact version. Claims distinguish implementation, measurement, simulation, and plans. Official instructions map to recorded passing conditions; missing mappings prevent ready status. Only explicitly requested supported formats are produced. Size violations, unsupported formats, and unverified page-count rules remain visible blockers. A manifest marked `ready_for_local_review` is neither a visual review nor an external submission receipt.

## Retrospective example

The [NASA Farm Navigators example](examples/nasa-farm-navigators/README.md) contains an official-source research record, a small playable learning prototype, acceptance conditions, a simulation plan, and tests. Its [integration record](examples/nasa-farm-navigators/validation.md) describes real Codex development/review and browser-driven simulation/report generation. Four internal prototype conditions passed; the output package correctly remained **not ready** for official submission because NASA data integration and official demo requirements were not satisfied.

The scenario was authored by AI for testing, not attributed to a real user's idea. Synthetic reactions are not real adoption estimates, and the closed 2025 challenge is not presented as a current opportunity.

## Compatibility and language

- **Instruction format:** Markdown with an [Agent Skills](https://agentskills.io/specification) entrypoint. Reusable across compatible hosts; equivalent behavior across all models is not guaranteed.
- **Research:** Requires host-provided web access and readable source materials.
- **Development and checks:** Require filesystem and execution tools supplied by the host.
- **Separate review:** Requires separate contexts or subagents. Otherwise, disclose that review shares the development context.
- **State helper:** Python 3.9+, macOS/Linux. Native Windows is not currently supported because the helper uses POSIX file locking.
- **Local web app:** The same Python requirement, a modern browser, and an installed, authenticated Codex CLI. Native Windows is not currently supported because process cancellation uses POSIX process groups.
- **Languages:** Instructions and code are English. User-facing communication defaults to Korean; follow explicit user language requests and official submission requirements.
- **Validation scope:** Automated component and subprocess integration tests plus a real Codex/browser retrospective example are available. Broad cross-host and cross-model validation is pending.

## Repository structure

```text
contest-copilot/
├── README.md
├── .github/workflows/checks.yml
├── contest-copilot/
│   ├── SKILL.md
│   ├── references/
│   │   ├── research.md
│   │   ├── idea-evaluation.md
│   │   ├── simulation.md
│   │   ├── validation-loop.md
│   │   └── local-workflow.md
│   ├── scripts/
│   │   ├── manage_state.py
│   │   ├── project_records.py
│   │   ├── simulate.py
│   │   └── build_submission.py
│   └── assets/
│       ├── report.html
│       └── submission-spec.json
├── web/
│   ├── server.py
│   ├── workflow.py
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── examples/nasa-farm-navigators/
└── tests/                  # State, records, simulation, submission, and web checks
```

## Roadmap

- [x] Define the research, idea assessment, simulation, and validation procedures.
- [x] Implement and test acceptance state, evidence freshness, iteration limits, and checkpoints.
- [x] Implement participant state, allowed actions, environment updates, and simulation rounds.
- [x] Provide a local chat, saved progress view, attachments, and stop-and-send feedback with Codex.
- [ ] Add web chat connectors for other agent applications.
- [x] Add evidence-linked Markdown/HTML reports and source ZIP packaging.
- [ ] Add native PDF, DOCX, and PPTX generation with rendered-format checks.
- [x] Publish a reproducible end-to-end example with actual execution evidence.
- [ ] Validate additional agent hosts and improve platform compatibility.

Roadmap items describe intended work, not available functionality.

## Feedback and contributions

[Open an issue](https://github.com/Evvvaaaaan/contest-copilot/issues) with your use case, host application, operating system, and the command or workflow that failed. For bugs, include expected behavior and a small reproduction with personal information removed. Discuss substantial changes before implementing them.

If this project is useful, a star helps others discover it. Concrete feedback and reproducible examples help improve the skill.

## Inspiration

[MiroFish](https://github.com/666ghj/MiroFish) inspired the idea of examining an idea through stateful stakeholder interactions. Contest Copilot is an independent project with its own instructions and local tools; it does not include the MiroFish application or require Zep. Its bounded actor/action engine is not a claim to reproduce all MiroFish functionality or predictive performance.

## Code Usage and Distribution

The project owner has not yet selected a software license for this repository. A software license specifies the conditions for using, modifying, and redistributing the code. This section records that pending decision; it does not grant additional reuse permissions.
