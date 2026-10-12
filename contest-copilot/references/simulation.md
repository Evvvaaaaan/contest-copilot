# Adaptive Stakeholder Simulation

Use this reference to compare shortlisted ideas through recorded interactions among simulated stakeholders. Adapt the environment to the idea: combine product use, adoption decisions, operational situations, and information exchange where they help answer the research questions. Present plans and findings to the user in Korean.

This file specifies behavior; it is not an executable simulator. Use only implemented local tools and supported host capabilities. If the required scripts or persistence mechanisms do not exist, identify the missing capability rather than inventing run outputs. Script and asset implementation is a separate authoring step.

## 1. Define the Experiment Before Running It

Read the shortlisted candidate versions, research evidence, user intent, official judging criteria, and agreed execution limits. Reuse settled decisions. Establish:

- The uncertainty being investigated and how it affects an official criterion or the user's intended outcome.
- The stakeholders affected directly or indirectly, including non-users where relevant.
- The situations in which the proposed mechanism could help, inconvenience, exclude, or fail participants.
- Observable simulated actions and outcomes that would support or challenge the candidate.
- Shared conditions, candidate-specific differences, stopping rules, and any planned sensitivity comparisons.

Keep the experiment separate from the desired conclusion. Do not write participant instructions that require them to praise the idea or produce a predetermined adoption rate. A useful experiment may reveal no clear preference or an unresolved tradeoff.

Choose participant count, rounds, activity scheduling, follow-up interviews, and repeat runs according to the question and agreed limits. Do not default to thousands of participants or claim that a larger population automatically improves validity. Changes to goals or limits require the user's decision; routine execution within the agreement does not.

## 2. Adapt the Environment to the Idea

Select situations from the actual problem rather than applying a universal social-media template.

| Context | Possible situations | Relevant interactions |
|---|---|---|
| Consumer application | Discovering the product, attempting a task, considering cost or continued use | Asking questions, trying, declining, seeking support, recommending or criticizing |
| Organizational tool | Evaluating adoption, integrating a workflow, handling operational burdens | User feedback, operator responses, purchasing or policy decisions |
| AI-assisted workflow | Encountering correct, incorrect, or uncertain outputs under declared scenarios | Accepting, verifying, correcting, escalating, or abandoning a task |
| Security product | Responding to a hypothetical alert or a permitted lab scenario | User action, analyst review, operator escalation, workflow friction |
| Ideathon proposal | Understanding the proposal and discussing feasibility or participation | Questions, objections, conditional acceptance, stakeholder negotiation |

These are design examples, not mandatory action lists. Include information exchange only where the scenario makes it plausible. Participants need not communicate with everyone or act every round. Allow inaction, postponement, partial adoption, and unresolved disagreement where meaningful.

Define the environment's resources, constraints, visibility rules, and action effects explicitly. Do not introduce unsupported capabilities simply to make the idea succeed. If prices, error rates, service delays, or other conditions are assumptions, label them and examine sensitivity when they matter.

An LLM-generated account of using a product is a simulated experience. Actual browser interactions, measured model outputs, or executed tests are a different evidence type. If real measurements are incorporated, link their version and source; do not relabel invented task outcomes as measured product behavior.

## 3. Construct Evidence-Informed Participants

For each participant, retain a stable ID and the information needed for decisions:

- Stakeholder role and relationship to the problem.
- Goals, constraints, relevant experience, and explicit tradeoffs.
- Initial knowledge, accessible resources, and relationships to other participants.
- Relevant research or user-provided evidence supporting the profile.
- Invented scenario details and uncertainties, clearly separated from evidence.
- Current state, memory, observations, and action history.

Prefer differences that affect decisions, such as budget, time, responsibility, access, or task needs. Avoid decorative personality labels that do not explain behavior. Do not infer preferences from demographic stereotypes or claim to reproduce a real individual's views from a fabricated profile.

Cover relevant perspectives using research and the experiment question. If population proportions are unknown, treat the composition as a scenario, not a representative sample. Do not manufacture demographic percentages or present synthetic participants as recruited users.

## 4. Separate LLM Decisions from Local Execution

The active host agent coordinates the experiment without requiring a separate LLM API key. It supplies each decision context to its available LLM execution capability and invokes local scripts to maintain the environment. A local script alone does not generate LLM decisions unless an explicitly available model interface has been implemented.

Define these responsibilities:

| Responsibility | Owner |
|---|---|
| Interpret a participant's situation and propose an allowed action | Host LLM |
| Select visible information according to declared rules | Local environment logic |
| Validate action fields, targets, and preconditions | Local code |
| Apply valid effects and maintain resources and relationships | Local code |
| Persist state and event records, count observable events | Local code |
| Interpret patterns, uncertainty, and implications | Host LLM using recorded evidence |

Provide a participant only the applicable profile, observations, memory, and allowed actions. Do not include other participants' private state or the evaluator's desired ranking in the decision input. If the host cannot provide separate contexts, document that limitation; limited prompts in one shared conversation are not guaranteed information isolation.

Keep evaluators' comparison notes separate from participant memory. Use a consistent decision-input structure across candidates so differences in prompting do not become an unacknowledged treatment.

## 5. Execute Recorded Rounds

For each candidate and run:

1. Save a run ID, candidate version, configuration, source references, host/model information when known, and execution status. Restore the agreed initial environment and participant state.
2. Select active participants using the declared schedule and state. Preserve the scheduling policy across candidates.
3. Construct each participant's visible observations from the environment. Include relevant earlier experiences without silently dropping material constraints.
4. Request an action with the required fields for its declared type. Include actor, target when applicable, parameters, and a concise stated reason or supporting observation references where useful.
5. Validate the action before changing state: actor and target exist, action is allowed, referenced observations are available, and required resources or preconditions hold.
6. If invalid, record the rejection and return the concrete validation error for correction within the retry limit. A rejected action must not change the environment or count as a successful outcome.
7. Apply accepted actions according to documented rules. Persist the action result and affected state, then update the relevant participant memories and shared observations.
8. Save a round checkpoint, inspect termination conditions, and continue within the agreed limits.

Choose whether participants act from one shared round snapshot or sequentially observe earlier actions in the same round. Document and preserve that choice across candidates. For simultaneous actions, define how conflicting resource use or targets are resolved rather than letting processing order silently decide the outcome.

Record actions only after execution or explicit rejection. Include run, candidate, round, actor, action, result status, affected objects, and traceable observation or evidence references. Preserve enough pre-state or checkpoint information to explain material state changes. On resumption, identify completed actions and avoid applying them twice.

When memory is summarized, preserve consequential experiences and links to the underlying events. Do not replace unfavorable events with optimistic summaries.

## 6. Keep Comparisons Fair and Reproducible

Use common baseline materials, stakeholder composition, decision-input format, environment rules, execution budgets, and scheduled external events where comparable. Document candidate-specific changes rather than pretending different mechanisms have identical conditions.

Restore participant memories and environmental state between candidates and independent repetitions. Never carry the first candidate's experience into a later candidate unless the experiment explicitly studies that sequence. Where order effects matter, vary or counterbalance candidate order within the budget and record it.

Record random seeds for local randomization when supported, but do not imply that a seed makes LLM outputs deterministic. Save configurations and logs so the procedure can be inspected and repeated even when outcomes vary.

Use sensitivity comparisons to test consequential assumptions, such as cost, error frequency, workload, or information visibility. Change identifiable conditions and explain which conclusions remain stable. Do not cherry-pick favorable runs or silently omit failures. If one candidate has incomplete execution, mark the comparison as incomplete rather than ranking it against a completed run as though exposure were equal.

## 7. Analyze Evidence and Interview Participants

Compute counts and rates from executed event records. State the numerator, denominator, participants exposed, and scenario conditions. Distinguish people, actions, and repeated interactions so one active participant does not become many independent observations.

Analyze benefits, burdens, acceptance conditions, objections, misunderstandings, operational friction, and conflicts between groups. Link each material conclusion to run and event IDs. Preserve minority reactions and unfavorable outcomes alongside common patterns.

Select follow-up interviewees because their recorded behavior is consequential, contrasting, or difficult to interpret. Ask neutral questions about the action and what conditions would change it. Keep interviews as post-run analysis unless the experiment explicitly allows them to affect later state. An interview response is a generated explanation, not proof of the true cause of earlier model behavior.

Separate:

- Recorded behavior inside the simulation.
- The LLM's interpretation of that behavior.
- Predictions that depend on assumptions.
- Findings from actual research, user feedback, or executed product tests.

Simulated acceptance is not real adoption, simulated task completion is not verified functionality, and agent agreement is not a calibrated probability. When results conflict with stronger real-world evidence, investigate the configuration and model limitations before drawing conclusions.

## 8. Stop, Report, and Feed Findings Back

Stop according to the agreed round, time, retry, and stagnation limits. A lack of new actions may indicate inactivity rather than social consensus. Record the reason for stopping, completed exposure, and whether the run is complete, partial, blocked, or failed. Reaching an execution limit does not establish that the idea passed validation.

Provide a Korean report containing:

- The question, candidate versions, participant composition, environment, and assumptions.
- Completed runs and rounds, execution limits, limitations, and evidence locations.
- Comparable findings by candidate and stakeholder group, including conflicting reactions.
- Sensitivity or repeat-run results when performed; otherwise state that variability was not evaluated.
- How findings affect the official-criterion assessment and the user's intended outcome.
- Proposed mechanism changes, unresolved hypotheses, and the next real-world or implementation check.

Use findings to revise the idea assessment and planning within the agreed scope. If a material revision changes what participants experience, rerun the affected comparison or label it as unverified for the new version. Request user input at the main skill's decision points, not after every participant action or round.
