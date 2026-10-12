---
name: contest-copilot
description: "Prepare or continue software and AI competition projects through deep research, user idea assessment, stakeholder simulation, iterative planning, development, validation, and submission preparation. Adapt to ideathons, security challenges, and other tracks based on the brief and user input. Agree on goals and acceptance criteria up front, improve autonomously until those criteria are met, then report results and collect user feedback."
---

# Contest Copilot

Develop the user's ideas into verifiable deliverables and submission materials using official judging criteria and evidence. Agree on goals and constraints at the start, iterate autonomously through planning, development, and validation, then present verified results. Do not request approval for every task.

## Language Policy

- Communicate with the user in Korean, including questions, progress updates, explanations, and review requests.
- Write skill instructions, internal technical references, code identifiers, code comments, and structured data keys in English.
- Use Korean for user-facing interfaces, review documents, and reports unless the user requests another language.
- Follow the competition's language requirements for final submissions.
- Preserve source quotations and user statements in their original language. Clearly label translations and interpretations.

## Scope and Execution Model

- Default to software and AI development competitions. Adapt to ideathons, security challenges, data analysis, or mixed tracks based on the brief and user requests. Do not force product development into an ideathon that does not require it.
- Respect requests limited to one phase. Do not modify code or restart the entire workflow when the user only requests an explanation or assessment.
- Default to personal use without a separate LLM API key. The LLM in the active host agent makes decisions; available search, file, browser, shell tools, and local scripts handle research, execution, persistence, and checks. Check the host's actual capabilities instead of assuming every model or application supplies these tools.
- Do not require the original MiroFish application or Zep. Implement stakeholder state, limited observations, actions, environment updates, repeated rounds, and analysis as local capabilities of this skill.
- Before execution, check which scripts actually exist and which tools are available. Do not claim to have executed an unimplemented tool or substitute imagined results for execution logs. Discuss API-dependent project features separately from the default workflow.
- Long-running work remains subject to usage limits and execution-environment constraints. Save the current state and resume point when interrupted. Do not imply that a skill file guarantees unlimited background execution.

## Working Record

Read existing competition materials, repositories, and user decisions first. Maintain a working record in the agreed project location, following existing documentation conventions when present. Establish the location if it is missing. Do not ask again for information the user already supplied.

Distinguish the following in the record:

- Official requirements, original sources, and dates checked.
- Research findings, counterevidence, AI interpretations, and unknowns.
- The user's ideas and experiences, AI proposals, final choices, and reasons for changes.
- Agreed scope, acceptance criteria, execution limits, and versions.
- Simulation configurations and action logs versus observations from the real world.
- Implementation status, executed checks, results and evidence, unfinished items, and next actions.

Link relevant code, materials, and logs by path. Do not invent user opinions or silently revise earlier decisions. Use detailed record and evaluation templates when those supporting files have been created.

For acceptance conditions, review iterations, evidence records, and resume points, use [scripts/manage_state.py](scripts/manage_state.py). Read the local state tool section in [the validation loop procedure](references/validation-loop.md) before first use. Store each competition's state in its project directory, not inside this skill. This helper records judgments and checks file freshness; it does not execute tests or authenticate approval.

## 1. Research the Competition and Its Context

Read [the research procedure](references/research.md) when starting or updating competition research. Investigate the competition and its surrounding context before assessing the user's ideas. Obtain the announcement URL, files, or competition name if missing.

Cover official requirements, organizer context, past winners, domestic and international alternatives, evidence of the problem, implementation conditions, and unresolved opportunities. Read primary materials, corroborate important claims, and investigate contradictions through repeated research passes.

Provide a Korean summary and detailed evidence, including sources, applicability, contradictions, and research gaps. Use coverage, the value of additional information, and agreed execution limits to determine when to stop; do not claim exhaustive coverage.

Present facts, existing approaches, unmet needs, and opportunity areas first. Do not introduce concrete AI-generated solution candidates until the user has shared their thoughts. Reuse thoughts already supplied instead of repeating intake questions.

## 2. Understand and Assess the User's Ideas

Read [the idea assessment procedure](references/idea-evaluation.md) when evaluating ideas or revising an assessment after new evidence. Present research findings, then ask about the user's problem framing, ideas, experiences, and intended impact. Reuse thoughts already shared and ask only for missing essentials. Summarize the user's intent for confirmation and compare it with the research.

Preserve the user's core problem and intended outcome. Propose substantial changes to the solution mechanism when supported by evidence, explaining what changed and why. Do not silently replace the user's purpose or treat a preferred technology as a non-negotiable requirement unless the user made it one.

Assessment priorities:

1. Mandatory official eligibility and submission requirements.
2. The competition's published judging criteria and weights.
3. Quality and differentiation evidenced by past winners and published judging comments.
4. Supporting evidence from domestic and international sources and simulations.

Official criteria take precedence. Do not treat a winner's characteristics as official requirements or proven causes of winning. Do not invent weights or probabilities of winning.

For each idea, explain strengths, weaknesses, feasibility, differences from prior work, and an evidence-backed recommendation: develop, revise and reassess, defer, or discard. State the conditions, assumptions, and uncertainty behind predictions. Propose research or experiments that could change the assessment. A recommendation to discard an idea does not authorize deleting the user's ideas or files.

## 3. Agree on Initial Plans and Execution Conditions

Shortlist promising candidates and begin with a one-page concept covering the problem, target users, proposed solution, differentiation, and connection to official judging criteria. Progressively elaborate necessary features, user flows, interfaces, technology, data, and validation methods. Do not lock every detailed specification at the outset.

Agree with the user up front on:

- Which candidates to compare, the user's core intent, and non-negotiable constraints.
- Project-specific evaluation items, measurement methods, targets, and required evidence aligned with official criteria.
- Mandatory conditions, optional improvements, and qualitative assessment methods.
- Time, round and retry limits, and stagnation criteria for research, simulation, and development loops.

Propose appropriate execution limits for each project and confirm them. Do not merge factual verification, functional test pass rates, AI model performance, and qualitative judging assessments into one accuracy score. An AI self-assessment score alone cannot establish a pass. For security challenges, also establish the authorized targets, environments, and actions.

Wait for the user's decision when initial conditions remain unanswered. Do not reconfirm settled conditions. Record and act within the scope of decisions explicitly delegated by the user.

## 4. Run the Custom Stakeholder Simulation

Read [the simulation procedure](references/simulation.md) when designing, running, or analyzing stakeholder experiments. Adapt the environment to the idea, combining use and adoption situations with information exchange where relevant. Do not force every experiment into a social-media setting.

Compare shortlisted candidates under equivalent conditions. Use research to construct users, non-users, operators, and affected groups, defining each participant's goals, constraints, relationships, and initial information. Separate evidence-backed characteristics from invented scenario settings.

Execution flow:

1. Isolate candidate environments and match participant composition, baseline materials, and execution scale. State which conditions necessarily differ between ideas.
2. Persist each participant's known information, observations, experiences, and action history.
3. Select the active participants and the information visible to them in the current situation.
4. Provide the LLM with the participant's profile, memory, observations, and allowed actions to determine an action.
5. Use local code to validate the action's structure, target, and compliance with environment rules before applying it. Do not log failed actions as successful.
6. Save environment changes and participant experiences, then advance to the next round.
7. Ask follow-up questions of simulated participants with notable reactions and analyze their responses alongside the complete record.

Limit the input supplied for each participant's decision. Do not claim guaranteed information isolation without an actually isolated execution environment. Do not equate more simulated participants with more independent samples or stronger real-world representativeness.

Link benefits, inconveniences, acceptance, objections, misunderstandings, conflicts of interest, and unexpected reactions to record IDs. Where useful and within agreed limits, repeat experiments to assess variability. Restore initial state for each candidate so memories from one candidate do not contaminate another comparison.

Distinguish simulated reactions from real user research. Do not present simulated occurrence rates as real adoption rates or purchase probabilities. If results conflict with real evidence, investigate the sources, configuration, and model limitations. Connect findings to official criteria to improve candidates and plans.

## 5. Iterate Autonomously Through Planning, Development, and Validation

Read [the validation loop procedure](references/validation-loop.md) when establishing acceptance checks, running implementation iterations, reviewing results, or resuming interrupted work. Separate development and review roles. Use a separate reviewer context when the host supports it; otherwise disclose the limitation and perform a distinct evidence-based review pass without claiming independent validation.

Elaborate the plan within the agreed scope and first build a minimal product with a working core flow. Incorporate evidence from simulations and real research. For ideathons or other tracks, produce the required proposal or prototype instead of imposing a software product.

- For existing projects, read applicable AGENTS.md instructions and execution guidance, and record relevant check results before changes. If a new project has no tests, state that and establish a validation method.
- For projects with a frontend, provide a preview address and describe current functionality as soon as an executable preview exists. Distinguish working features, work in progress, and placeholder data.
- Show progress without waiting for approval of each small task. Incorporate feedback received during execution and record why changes were made. Explain the impact and seek confirmation for decisions that change the agreed core purpose or scope.
- When checks fail, reproduce the failure and establish its cause before revising the relevant plan or implementation. Rerun the original failing check and affected checks after changes.
- After two consecutive unsuccessful fixes to the same problem, revisit the causal hypothesis. On reaching agreed stagnation criteria or execution limits, report the current result, unmet conditions, and decisions needed.
- Evaluate AI models using agreed data and measurement conditions, preventing evaluation-data leakage. Exercise actual functional flows. Disclose the rubric and evidence for qualitative assessments; do not present them as official judging outcomes.
- Do not delete tests or lower targets to obtain a pass. When new conditions are needed, explain why and how they affect the project, then obtain the user's decision.

For each iteration, save the target version, changes, executed checks, actual outputs or logs, per-condition verdicts, and next actions. Mark checks that cannot run because of missing tools, data, or permissions as unverified.

## 6. Request User Feedback After Meeting the Criteria

Once the agreed acceptance criteria are met, present reviewable deliverables, key changes, verification evidence, and remaining limitations, then request feedback. Do not repeatedly ask the user to approve unfinished intermediate work. If progress is blocked or a limit is reached before meeting the criteria, report the result as incomplete.

Distinguish change requests, goal changes, and final acceptance in user feedback. For change requests, iterate again while retaining the agreed criteria. If goals change, reconfirm only the affected conditions. If the user has not answered, wait for the relevant feedback instead of assuming final approval.

## 7. Finalize Deliverables That Match the Actual Results

After the user accepts the result, create the required report, presentation, demo, source package, executable, or other deliverables according to the latest official submission instructions and templates. Do not generate a standard bundle of unrequested outputs.

- Explain how the user's ideas and choices shaped the problem definition, plan, and implementation.
- Distinguish plans, actual implementation, measured results, simulations, and expected future benefits. Do not fabricate performance figures, interviews, or implemented features.
- Align submission claims, numbers, and screenshots with the accepted implementation version and link supporting evidence.
- Generate actual files in the required formats, then open or render them to inspect the output. Check length, size, filenames, required attachments, and reproducibility instructions.
- If required formats cannot be produced with available tools, do not label a text draft as the completed deliverable.
- Provide artifact links, actual check results, remaining issues, and items requiring user review. Update connected submission materials when feedback changes the result.
- Perform actual submission, deployment, or email delivery only with authorization for that action. Distinguish submission readiness from completed submission supported by receipt evidence.
