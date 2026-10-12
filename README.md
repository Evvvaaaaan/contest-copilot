<div align="center">

# Contest Copilot

**Turn competition briefs and your ideas into evidence-backed projects.**

An agent skill for deep research, idea assessment, and iterative development with recorded verification.

[![Checks](https://github.com/Evvvaaaaan/contest-copilot/actions/workflows/checks.yml/badge.svg)](https://github.com/Evvvaaaaan/contest-copilot/actions/workflows/checks.yml)
![Status: Early development](https://img.shields.io/badge/status-early_development-orange)
![Python: 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
[![GitHub stars](https://img.shields.io/github/stars/Evvvaaaaan/contest-copilot?style=social)](https://github.com/Evvvaaaaan/contest-copilot/stargazers)

[Get started](#get-started) · [What works today](#what-works-today) · [Workflow](#workflow) · [Roadmap](#roadmap)

</div>

## Why Contest Copilot?

Competition preparation involves more than generating an idea. You need to understand the judging criteria, investigate previous winners, preserve your own perspective, build something feasible, and support the final claims with evidence.

Contest Copilot gives an AI agent a reusable procedure for that work. Agree on the purpose, acceptance conditions, and execution limits first. Let the agent iterate within those boundaries, then review the result when the required conditions are met.

**This is an early skill and a working local state helper. It is not yet a complete autonomous competition platform.** The stakeholder simulator, progress dashboard, and submission generators are not implemented.

## What works today

| Capability | Current status |
|---|---|
| Competition research and source checking | Agent instructions written |
| Evidence-based idea assessment | Agent instructions written |
| Adaptive stakeholder simulation | Procedure written; execution engine not implemented |
| Development and separate review | Workflow written; depends on host tools |
| Acceptance contracts and review iterations | Working Python CLI |
| Verdicts, evidence hashes, and change detection | Working Python CLI |
| Checkpoints and decision history | Working Python CLI |
| Live progress dashboard | Planned |
| Report and presentation generation templates | Planned |
| End-to-end competition case study | Not yet validated |

The state helper does not call an LLM API. Your existing agent supplies reasoning and executes checks; the helper stores results and checks whether recorded files have changed. Your agent's subscription, tool availability, and usage limits still apply.

## Workflow

1. **Research the competition.** Read the announcement, amendments, eligibility rules, judging criteria, previous winners, and domestic and international evidence. Follow primary sources and record gaps and contradictions.
2. **Understand your idea.** Hear your problem framing and experience before proposing concrete solutions. Preserve your intended outcome while considering better ways to achieve it.
3. **Agree on an execution contract.** Define mandatory conditions, methods, targets, evidence, and iteration limits. Official requirements take precedence over inferred patterns from winners.
4. **Design stakeholder experiments.** Compare shortlisted ideas through relevant usage, adoption, and information-exchange scenarios. The procedure is available; an executable simulator is still on the roadmap.
5. **Iterate through planning, development, and review.** Build the smallest useful core flow. Review actual evidence, address failures, and repeat within the agreed limits. Make a running frontend available for feedback when the host and project support it.
6. **Report and collect feedback.** Report after required conditions pass, or report incomplete status when blocked or limited. Incorporate feedback without silently changing the user's purpose.
7. **Prepare the required submission.** Match claims and deliverables to the accepted implementation, measured results, and official format. External submission requires authorization.

Simulated reactions are not real user research. A successful CLI invocation is not a passing product test. An LLM's self-assigned score is not evidence that a requirement has been met.

## Get started

### 1. Download the repository

```sh
git clone https://github.com/Evvvaaaaan/contest-copilot.git
cd contest-copilot
```

### 2. Load the skill in your agent

The installable skill folder is **`contest-copilot/`**, inside the repository. Register that folder using your agent's supported skill installation mechanism, or ask a file-capable agent to read its entrypoint:

```text
Read contest-copilot/SKILL.md and follow the relevant references.
Help me prepare for this competition: [announcement URL or file].
Begin with research. Preserve my ideas and record evidence.
Agree on acceptance criteria and execution limits before development.
```

Host applications have different discovery paths and capabilities. Loading the repository does not automatically install or activate a skill in every AI application.

### 3. Check the local helper

With Python 3.9+ on macOS or Linux:

```sh
python3 contest-copilot/scripts/manage_state.py --help
python3 -m unittest discover -s tests -v
```

No third-party Python packages are required for these commands. Tests use temporary project files and exercise the actual CLI in separate processes.

For the contract schema and command examples, read [Local State Tool](contest-copilot/references/validation-loop.md#9-local-state-tool).

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

`ready_for_user_review` means all required conditions have recorded, current passes. It does not authenticate those judgments or mean the user has accepted the result. `limit_reached` means no new review iteration can start under the current allowance; the current review can still finish.

Only registered files are fingerprinted. Reviewers must separately check unlisted files, external services, runtime conditions, and whether the evidence actually proves the target. Time, retry, and stagnation limits remain the coordinating agent's responsibility.

Keep competition-specific state, source materials, and evidence in a separate project directory. They are not part of this reusable skill.

## Compatibility and language

- **Instruction format:** Markdown with an [Agent Skills](https://agentskills.io/specification) entrypoint. Reusable across compatible hosts; equivalent behavior across all models is not guaranteed.
- **Research:** Requires host-provided web access and readable source materials.
- **Development and checks:** Require filesystem and execution tools supplied by the host.
- **Separate review:** Requires separate contexts or subagents. Otherwise, disclose that review shares the development context.
- **State helper:** Python 3.9+, macOS/Linux. Native Windows is not currently supported because the helper uses POSIX file locking.
- **Languages:** Instructions and code are English. User-facing communication defaults to Korean; follow explicit user language requests and official submission requirements.
- **Validation scope:** Local CLI tests are available. Broad cross-host and cross-model validation is pending.

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
│   │   └── validation-loop.md
│   └── scripts/
│       └── manage_state.py
└── tests/
    └── test_manage_state.py
```

## Roadmap

- [x] Define the research, idea assessment, simulation, and validation procedures.
- [x] Implement and test acceptance state, evidence freshness, iteration limits, and checkpoints.
- [ ] Implement participant state, allowed actions, environment updates, and simulation rounds.
- [ ] Provide progress views and feedback integration.
- [ ] Add deliverable templates matching competition requirements.
- [ ] Publish a reproducible end-to-end example with actual execution evidence.
- [ ] Validate additional agent hosts and improve platform compatibility.

Roadmap items describe intended work, not available functionality.

## Feedback and contributions

[Open an issue](https://github.com/Evvvaaaaan/contest-copilot/issues) with your use case, host application, operating system, and the command or workflow that failed. For bugs, include expected behavior and a small reproduction with personal information removed. Discuss substantial changes before implementing them.

If this project is useful, a star helps others discover it. Concrete feedback and reproducible examples help improve the skill.

## Inspiration

[MiroFish](https://github.com/666ghj/MiroFish) inspired the idea of examining an idea through stateful stakeholder interactions. Contest Copilot is an independent project with its own instructions and helper; it does not include the MiroFish application or require Zep. The original project's functionality is not claimed as implemented here.

## License

A reuse license has not yet been selected for this initial publication.
