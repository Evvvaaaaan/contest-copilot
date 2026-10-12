# Evidence-Based Idea Assessment

Use this reference after presenting competition research and hearing the user's perspective, or when new research, simulation, or implementation evidence requires reassessment. Explain assessments and ask questions in Korean. Preserve the original language of user statements and source quotations.

## 1. Establish the User's Intent

Read the research findings, official criteria, and existing user decisions. Ask only for missing information that materially affects the assessment. Do not propose new solution candidates before hearing the user's thoughts.

Distinguish:

- **Core problem:** the situation the user wants to change and why it matters to them.
- **Intended outcome:** what should improve and for whom.
- **Proposed mechanism:** how the current idea attempts to produce that improvement.
- **Constraints:** explicit requirements such as target group, time, resources, accessibility, or a required technology.
- **Preferences and assumptions:** choices the user favors and beliefs that still need evidence.

Summarize the user's intent and resolve material ambiguity. Reuse explicit prior statements instead of forcing another confirmation of settled intent. Mark an inferred intention as an AI interpretation until confirmed. Separate the user's personal experience from evidence about a wider population.

## 2. Preserve the Problem, Allow the Solution to Change

The user permits substantial changes to the solution while preserving their core problem and intended outcome. A new mechanism may replace the originally suggested technology, interface, feature set, or delivery model when evidence supports the change and explicit constraints still hold.

For each substantial alternative, explain:

1. Which user problem and outcome remain unchanged.
2. What changes from the original proposal.
3. Which evidence or failed assumption motivates the change.
4. How the alternative better addresses official criteria or demonstrated needs.
5. What tradeoffs, uncertainties, and new validation needs it introduces.

Do not turn a named technology into a fixed requirement unless the user made it one. Conversely, do not discard explicit constraints to make a preferred alternative easier to build. A change to the core problem, target group when explicitly fixed, or agreed purpose requires the user's decision.

If evidence challenges the problem itself, explain the conflict rather than preserving a false premise or silently substituting a different problem. Keep the original proposal and its version in the record even when recommending a different mechanism.

## 3. Apply the Agreed Evaluation Hierarchy

Evaluate mandatory official requirements first. For each, distinguish `meets`, `does_not_meet`, and `unknown`, with the relevant source and reason. Missing evidence is not proof of either compliance or noncompliance. An unresolved mandatory condition prevents an unconditional eligibility or readiness claim.

Then assess the idea against the competition's published judging criteria. Use official weights only when they exist. If the organizer provides a rubric, preserve its definitions. If an internal rubric is needed, label it as an AI-proposed working rubric and agree on it with the user before treating it as an acceptance gate.

Use past winners and published judging comments as comparative evidence for implementation quality, validation depth, and differentiation. They do not override the current official criteria. Account for changed tracks, conditions, or technical baselines.

Use domestic and international research and completed simulations as supporting evidence. Do not fabricate a probability of winning or imply access to unpublished judging decisions.

For each official criterion, retain:

| Field | Content |
|---|---|
| Criterion | Official wording, source, and published weight if any |
| Current assessment | Strength, weakness, unmet condition, or unknown |
| Evidence | Research findings, user statements, inspected artifacts, or executed results |
| Interpretation | Why that evidence matters to the criterion |
| Gap | What remains unproven or contradictory |
| Next check | The observation or experiment that could change the assessment |

Keep criterion coverage, evidence strength, and measured performance distinct. A weighted internal score, when agreed, remains an assessment aid rather than an official result; it cannot cancel a failed mandatory requirement or turn unknowns into passes.

## 4. Compare Feasible Alternatives

Compare the original proposal with evidence-backed alternatives that preserve the same intent. Generate enough alternatives to expose meaningful tradeoffs, but do not force a fixed number of weak variants or pad the shortlist with cosmetic differences.

Use the research to examine:

- Whether the problem is demonstrated for the intended users.
- Whether the proposed mechanism plausibly addresses the cause of that problem.
- Differences from existing products, research, and relevant winning entries.
- Data access, integration requirements, technical feasibility, and development resources.
- Whether the required level of implementation and validation is achievable before the deadline.
- Who benefits, who bears burdens, and which assumptions need stakeholder investigation.

Adapt the evidence to the track. An ideathon may demonstrate feasibility without a production implementation. An AI project needs a credible data and evaluation plan. A security entry must fit the task's authorized environment and validation requirements. Do not rank by technical complexity or use of AI alone.

Distinguish a previous solution's existence from proof that an idea has no value. Identify whether the proposed context, target population, measurable improvement, or delivery method changes the comparison. Record when novelty or differentiation remains unsubstantiated.

## 5. Make Recommendations with Reversal Conditions

Use the following recommendation categories without treating them as irreversible decisions:

| Recommendation | When it is justified | What must accompany it |
|---|---|---|
| Develop | The candidate has sufficient fit and a feasible route to address remaining uncertainties | Strengths, remaining assumptions, and the next validation steps |
| Revise and reassess | A specific weakness can plausibly be resolved while preserving the user's intent | The proposed change, evidence behind it, and a check for improvement |
| Defer | A material unknown, unavailable resource, or timing issue prevents a sound current decision | The missing evidence or resource and a concrete condition for reconsideration |
| Discard recommendation | Evidence indicates a fundamental mismatch, infeasibility within constraints, or inadequate value that feasible revisions do not resolve | Sources, the scope of rejection, and what evidence could reverse the recommendation |

Do not recommend discarding an idea merely because information is missing. Distinguish a fundamental issue from a temporary implementation limitation. State whether the recommendation rejects one mechanism, its current scope, or participation in the selected track; do not automatically reject the underlying user problem.

Keep facts, interpretations, and forecasts separate. For a forecast, explain its assumptions, applicable conditions, supporting evidence, and uncertainty. Do not manufacture precise probabilities or treat model agreement as calibrated confidence.

Each recommendation must explain what would change it. Prefer a focused research step, prototype, or measurable experiment over vague instructions to gather more information. Preserve counterevidence and the user's disagreement in the record.

## 6. Hand Off Promising Candidates to Simulation

Make a provisional shortlist using official criteria and research before running stakeholder simulations. Label the assessment as preliminary when the simulation or feasibility evidence is still pending. Do not claim that a simulation has confirmed a candidate before an actual run exists.

For each candidate, provide:

- Candidate ID and version, the original user idea it develops, and the intent preserved.
- The problem, proposed mechanism, explicit constraints, and evidence-backed differentiators.
- Candidate-specific assumptions and unresolved stakeholder questions.
- Which inputs and conditions must be shared across candidates for a fair comparison.
- Which observations would support or challenge the candidate and how they relate to official criteria.

Run comparisons within the agreed scope and execution limits using [the simulation procedure](simulation.md). Do not add a dependency on the original MiroFish application or an external LLM API.

After actual results are available, link conclusions to run IDs, configurations, and relevant event records. Compare them with the earlier assessment and real-world evidence. A favorable simulation does not establish real adoption, validate technical performance, or remedy failed official requirements.

If a revised mechanism materially changes what participants experience, do not reuse an old simulation as evidence for the new version. Identify affected findings and rerun the necessary comparison within the agreed limits, or mark the new version as unverified.

## 7. Report at Meaningful Decision Points

Maintain a record of the original user intent, candidate versions, supporting and conflicting evidence, recommendation changes, and reasons. Clearly label an AI-proposed alternative even if it develops the user's original idea. Attribute the user's contributions accurately.

Explain the assessment in Korean with:

1. The user's core problem and intended outcome as understood.
2. A comparison against official requirements and judging criteria, supported by research and winner analysis.
3. The original mechanism and any proposed replacements, including preserved intent and tradeoffs.
4. Recommendations, assumptions, uncertainty, and evidence that could change the conclusions.
5. The provisional shortlist or updated findings from completed simulations.
6. The specific user decision needed, if any.

Use initial alignment and the main skill's acceptance criteria to determine when feedback is needed. Do not ask for approval of every internal comparison or alternative. During an autonomous loop, revise within agreed boundaries and report when criteria are met, a meaningful scope decision is required, or execution is blocked or limited. Do not assume approval from silence or interpret a discard recommendation as permission to delete work.
