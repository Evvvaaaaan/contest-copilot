# Development and Independent Review Loop

Use this reference to turn agreed competition goals into measurable acceptance conditions, iterate on implementation, review evidence, and report results. Keep development and review responsibilities separate. Communicate with the user in Korean and follow the main skill's language and authorization rules.

This document defines the workflow. It does not itself run tests, persist checkpoints, or create autonomous background execution. Check the available tools and implemented scripts before claiming any of those capabilities.

## 1. Establish the Acceptance Contract

Read the official requirements, research, user intent, selected concept, relevant simulation findings, and existing project state. Propose project-specific conditions and execution limits for initial user agreement; reuse conditions already settled.

For every acceptance condition, record:

| Field | Purpose |
|---|---|
| ID and source | Trace the condition to an official requirement, user decision, or explicitly agreed internal target |
| Requirement | Describe the observable behavior, artifact, or quality being evaluated |
| Required status | Distinguish mandatory conditions from optional improvements |
| Method | Identify the actual command, user flow, experiment, inspection, or anchored review rubric |
| Target | Define the pass condition, including applicable units, denominators, and comparison baselines |
| Evidence | Specify the output, log, artifact, measurement, or observation needed |
| Applicability | State the track, scenario, environment, and version to which the condition applies |

Keep official judging criteria and weights distinct from internal measurements. An agreed internal rubric is not the organizer's score. Separate functional correctness, factual accuracy, AI performance, and qualitative quality rather than combining them into an undefined accuracy percentage.

Define time, iteration or retry limits, and observable stagnation conditions for the project. Include simulation and review work in the relevant budget. A limit determines when to stop and report; it does not make unfinished work acceptable.

Do not lower a target or remove a required check to obtain a pass. Record and obtain the user's decision for changes to agreed acceptance conditions. Optional exclusions need an explicit reason and applicable user decision; official mandatory requirements cannot be waived by an internal score or preference.

## 2. Assign Development and Review Responsibilities

The development role plans within scope, builds the smallest working core flow, performs appropriate checks, and supplies a reviewable artifact and evidence. It may suggest changes to the plan but cannot approve its own unsupported success claims.

The review role evaluates the artifact against the acceptance contract. It inspects relevant files, examines raw outputs, and executes targeted checks when necessary to establish behavior. It reports findings and per-condition verdicts rather than implementing fixes in the product.

When the host supports subagents or separate contexts, use a separate reviewer context. Supply the reviewer with:

- The user's intent and agreed requirements, including official sources when relevant.
- The artifact version, relevant implementation or deliverables, and execution instructions.
- Inputs, environment information, baseline failures, and raw verification evidence.
- Review scope and execution limits.

Do not instruct the reviewer to agree with the developer's conclusion or give it an expected overall verdict. Provide known limitations for investigation without hiding unfavorable evidence. The reviewer may use isolated scratch files for checks but should not mutate the product or agreed acceptance tests during review.

If separate contexts are unavailable, use an explicit review pass after development and disclose that it shares context. Do not claim independent review. Separate roles do not imply separate model families, statistically independent judgments, or a need for an external API key.

Avoid concurrent edits to an artifact under review. Bind findings to a stable revision or file snapshot. If files change during a relevant check, identify the mismatch and rerun affected verification before accepting the result.

## 3. Establish a Baseline and Build a Minimal Product

Read applicable AGENTS.md instructions and existing architecture, dependencies, and test commands. Run relevant existing checks before modifying the project and preserve their actual output. Do not attribute pre-existing failures to the new change or silently treat them as acceptable when they affect a mandatory condition.

For a new project without tests or an executable artifact, record that state and establish meaningful checks as the core flow is built. Do not invent a passing baseline. Add tests that verify important behavior or invariants, not tests that merely mirror the implementation.

Start with a minimal product whose core flow works end to end. For non-product tracks, build the corresponding proposal, prototype, analysis, or demonstration required by the competition. Elaborate the one-page concept progressively rather than requiring approval of every implementation detail.

For projects with a frontend, provide an accessible preview once it runs, explain what currently works, and identify placeholder data or unfinished features. Show progress without stopping for routine approval. Incorporate unsolicited user feedback within scope; ask only about changes to the agreed core purpose, explicit constraints, or limits.

## 4. Run the Iteration

For each iteration:

1. Read the current checkpoint, acceptance contract, unresolved review findings, and latest user feedback.
2. Choose changes that address observed failures or the most consequential unmet conditions. Preserve the user's core problem and intended outcome.
3. Investigate failures before fixes. Reproduce the behavior, inspect complete errors and relevant code, and state an evidence-backed cause.
4. Implement the smallest relevant change and run checks appropriate to that change.
5. Freeze a reviewable version and give the review role the artifact and evidence.
6. Have the reviewer assess the conditions, reproduce consequential findings, and identify missing or stale evidence.
7. If conditions remain unmet, use the findings to revise the plan or implementation and repeat within the agreed limits.
8. If all agreed required conditions are met, prepare the user-facing result and pause for feedback at the main skill's decision point.

Do not wait for user approval between internal development and review passes. A dispute between roles must be resolved through the agreed requirement and additional evidence, not majority voting or forced agreement. If the requirement itself is ambiguous, ask the user the specific question needed to resolve it.

## 5. Require Evidence Appropriate to the Claim

| Claim | Required evidence |
|---|---|
| A build succeeds | An actual build on the relevant version completed successfully |
| A bug is fixed | The original reproduction now succeeds, with affected checks evaluated |
| A feature works | The actual input-to-output flow was exercised under the stated conditions |
| AI performance meets a target | Results from the agreed dataset, metric, baseline, and measurement conditions |
| A submission artifact is complete | The required file exists, opens or renders correctly, and meets the specified format and content requirements |
| A qualitative criterion is met | A criterion-based review with observable evidence and explicit limitations |

For AI work, separate development feedback data from final evaluation data where applicable. Do not tune repeatedly against a claimed untouched test set. Record data versions, sample sizes, metrics, and test conditions. A favorable simulation or fluent explanation cannot substitute for measured model performance.

For security work, validate only in the authorized environment and scope. For frontend work, inspect the relevant user flows and rendered result; static type checks alone do not establish usability. For reports, verify factual claims and their supporting sources as well as the file format.

Avoid repeating broad suites without a new change, failure, or unresolved concern. Rerun the original failing check and checks affected by a fix. When new output would not resolve an uncertainty, stop redundant testing and proceed to the next meaningful step.

## 6. Record Verdicts and Findings

Use per-condition verdicts:

- `pass`: the target is met with applicable evidence for the reviewed version.
- `fail`: observed behavior or output contradicts the target.
- `unverified`: evidence is missing, stale, blocked, or insufficient to decide.
- `waived`: an optional condition was explicitly excluded by an applicable user decision; record the reason. This is not a passing result.

A failed or unverified required condition prevents overall acceptance. Do not hide a mandatory failure inside an aggregate pass rate. Exclude waived optional conditions transparently rather than counting them as passed. Keep qualitative assessments labeled as assessments, not objective measurements or official judging outcomes.

For each finding, record the condition ID, artifact version, reproduction or inspection method, expected behavior, actual observation, evidence location, consequence, and suggested next investigation. The developer determines the implementation change; the reviewer checks whether the finding is resolved on the new version.

Retain prior verdicts as history. Invalidate evidence affected by a change and recheck it. Carry forward unaffected evidence only when its applicability is explained. Reviewer-created checks must test the agreed requirements rather than silently expand the project or introduce new acceptance thresholds.

## 7. Detect Stagnation and Preserve Resume State

After two consecutive unsuccessful fixes to the same issue, revisit the causal hypothesis before another patch. Distinguish implementation defects from wrong assumptions, unavailable data, environment failures, and an infeasible target. Do not treat every failure as a reason to rewrite the project.

Track progress against unresolved required conditions and the project's agreed stagnation rule. Reach the limit, save state, and report the unmet conditions and available choices; do not continue indefinitely or announce success to escape the loop.

At meaningful checkpoints, save:

- Current concept and artifact versions, acceptance-contract version, and preserved user intent.
- Iteration status, outstanding findings, executed checks, and evidence paths.
- Changes made, their causes, and resulting verdicts.
- Time or iteration budget used when observable and remaining limits.
- Pending user decisions, current environment or preview information, and the next executable action.

On resumption, verify that files and environment still match the checkpoint. Resume from unresolved work without duplicating completed mutations or treating old results as current. Record interruptions, unavailable tools, and authentication or permission barriers honestly.

## 8. Report Results and Incorporate Feedback

When required conditions are met, provide the user with reviewable deliverables or a working preview, the criteria and actual results, separate review findings, material limitations, and the impact of the user's ideas and feedback. Do not present an unimplemented feature or future goal as complete.

Request feedback at that point. If the user asks for changes within scope, incorporate them and repeat affected development and review. If goals or thresholds change, revise only the affected agreement and preserve its history. If the user accepts the result, proceed to the main skill's submission preparation phase.

If blocked or limited before acceptance, report incomplete status, actual failure output or evidence, completed work, unmet conditions, and the precise decision or resource needed. Do not seek routine approval merely because an internal iteration failed.

Apply relevant checks again to generated submission materials. Development acceptance, submission readiness, and confirmed external submission are distinct states. Final packaging must match the accepted implementation and measured results.

## 9. Local State Tool

Use `scripts/manage_state.py` with Python 3.9+ on macOS/Linux. It uses only the standard library, requires no LLM API key, and serializes CLI access with a lock. Write all project-specific state, contracts, and evidence outside the skill directory. Relative artifact and evidence paths resolve against the stored project root; the state and contract CLI paths resolve against the current working directory.

Create a JSON acceptance contract from the actual user agreement. The following is a schema example, not a preapproved target or a template to apply without adaptation:

```json
{
  "project": "Competition project name",
  "intent": "The user's core problem and intended outcome",
  "max_iterations": 5,
  "conditions": [
    {
      "id": "core-flow",
      "source": "Official requirement or user agreement reference",
      "required": true,
      "requirement": "Describe the observable required behavior",
      "method": "Describe the agreed check",
      "target": "Describe the pass condition and applicable measurement units",
      "applicability": "Scenario, environment, and scope"
    }
  ]
}
```

Invoke the helper with an absolute script path, replacing the example project paths. Commands below assume the working directory is the skill directory:

```sh
python3 scripts/manage_state.py --state /project/progress.json init --project-root /project --contract /project/contract.json --decision "Reference to the user's initial agreement"
python3 scripts/manage_state.py --state /project/progress.json checkpoint --phase development --next-action "Implement the core flow" --note "Initial plan agreed"
python3 scripts/manage_state.py --state /project/progress.json start --version iteration-1 --artifact src/main.py --artifact tests/test_core.py
python3 scripts/manage_state.py --state /project/progress.json record --condition core-flow --verdict pass --method "Actual command or inspection performed" --note "Observed result and limitations" --review-mode shared_context --evidence evidence/core-flow.log
python3 scripts/manage_state.py --state /project/progress.json status
python3 scripts/manage_state.py --state /project/progress.json history
```

Run real checks and save their raw output before using `record`; the example does not execute a test. `--review-mode separate_context` is valid only when a separate reviewer actually performed the review. Neither that flag nor `--decision` proves role isolation or user approval. Cite the actual conversation decision; do not invent one.

Call `start` when an implementation is ready for its next review. Include every relevant source, configuration, data manifest, dependency lockfile, and test file using repeated `--artifact` arguments. It snapshots named files, starts a numbered review iteration, and resets current verdicts. Fixes to a reviewed snapshot require a new iteration. Earlier verdicts remain in history. The script cannot detect changes in unlisted files, external services, or the runtime environment; the reviewer must check those explicitly.

`record` accepts `pass`, `fail`, `unverified`, and `waived`. A pass requires an existing evidence file. Required conditions cannot be waived; optional waivers require a decision reference. Record observations and unresolved findings in `--note`, and the executed command or inspection in `--method`. The script checks file hashes, not whether the evidence substantively proves the target. Qualitative and numeric judgments remain the reviewer's responsibility.

`status` derives acceptance rather than accepting an overall pass flag. All required conditions must pass on the current contract and artifact snapshot. Modified or missing artifact/evidence files invalidate applicable results. `ready_for_user_review` is not final user acceptance or confirmed submission. `limit_reached` means the iteration allowance is exhausted and required conditions remain unmet; the current iteration can still finish its review, but another iteration cannot start. A successful status command exits zero even when acceptance is unmet; consumers must read the JSON `status` and `unmet_required` fields.

Save a `checkpoint` at meaningful boundaries with phase, next action, blockers or pending decisions in `--note`, and an optional `--preview-url`. On resumption, read `status`, inspect the checkpoint and file freshness, and use `history` when earlier reasoning is needed. A checkpoint does not resume execution automatically. Before the first review iteration, its snapshot-match flag is false because no artifact snapshot exists yet.

Revise a contract only after a real user decision using `contract --contract /project/revised-contract.json --decision "Decision reference"`. Revisions preserve old contracts and results, invalidate previous acceptance, and do not reset the iteration count. The tool enforces the agreed iteration ceiling; time, retry, and stagnation limits still require the coordinating LLM to monitor and record them. It does not provide a dashboard, background loop, simulation engine, or automatic test runner.
