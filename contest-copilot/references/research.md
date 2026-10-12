# Competition Research Procedure

Use this reference when researching a competition or updating research after material changes. Its purpose is to help the user deeply understand the competition and its context before proposing or evaluating solutions. Follow the skill's language policy: instructions are in English; explanations and research deliverables for the user are in Korean.

## 1. Establish the Research Map

Read the materials and decisions already provided. Identify the exact competition edition, track, organizer, and current official announcement. Obtain missing identity information before attaching rules or past winners to the project. Do not mix similarly named competitions or editions.

Inspect official announcements, attached documents, submission templates, amendments, and FAQs. Record the current deadline and time zone. Check whether a newer official notice supersedes an older document; preserve unresolved conflicts rather than silently choosing a convenient version.

Build a research map around questions, not a list of links:

| Area | Questions to resolve |
|---|---|
| Official requirements | What must be submitted? Who is eligible? What conditions can disqualify an entry? |
| Judging | What is assessed, with which published weights and procedures? |
| Organizer context | What purpose and problem does the organizer explicitly identify? |
| Past winners | What won, what was implemented, and what was actually validated? |
| Domestic and international landscape | Who addresses the same problem, and how? |
| Problem evidence | Who experiences the problem, in what circumstances, and with what consequences? |
| Implementation conditions | Can the required data, technology, resources, and environment be obtained? |
| Gaps and opportunities | What remains unresolved, disputed, or insufficiently supported? |

For each question, record its decision relevance, evidence found, unresolved issue, and next research action. Use statuses such as `confirmed`, `needs_research`, `no_public_evidence_found`, and `conflicting`. Distinguish a confirmed fact from a research area that merely has some coverage.

Use existing project-specific time limits and stopping conditions. If limits have not yet been agreed, include a proposed research boundary in the initial intake rather than silently committing to unlimited research. Continue independent, reversible investigation while a decision is pending when it does not depend on that answer.

## 2. Search Broadly and Follow Evidence Trails

Search in Korean and English, adding relevant local terminology and languages when the competition or domain warrants it. Adapt search terms as the field's terminology becomes clear. Search by both the proposed technology and the underlying problem; the best available solution may use a different technology.

Starting query patterns, to adapt rather than execute mechanically:

```text
"[competition name]" 공고 심사기준 FAQ
"[competition name]" 역대 수상작 대상 최우수상
"[winning team or project]" 발표 시연 GitHub
"[problem or domain]" 실태조사 통계 사용자 불편
"[English domain terms]" challenge winners
"[problem]" benchmark dataset limitations
"[existing service]" evaluation complaints alternatives
```

Follow useful discoveries beyond the initial result:

- From an award announcement, identify the team or project and inspect available presentations, demos, repositories, interviews, and subsequent products.
- From a paper, inspect the evaluation design, datasets, baselines, limitations, and relevant prior or follow-up work.
- From a product, inspect documentation, actual accessible functionality, independent evaluations, and user complaints where relevant.
- From a statistic or news article, trace the claim to the original survey, dataset, announcement, or report.

Maintain a compact search trail of the question, query or source path, useful findings, remaining gap, and reason for further searching. Avoid collecting unrelated links simply to inflate coverage. When archives are accessible, follow earlier competition editions and explain the historical period covered and its relevance to current criteria.

## 3. Extract Evidence from Original Materials

Open and read supporting material. Search snippets help locate sources but do not establish that a claim has been verified.

- **Announcements and PDFs:** inspect relevant text, tables, footnotes, attachments, and revision dates. Use rendered pages where text extraction misses important content.
- **Papers and statistics:** record the population, sample, measurement method, geography, period, comparison conditions, and limitations.
- **Open-source projects:** inspect the relevant implementation, runtime requirements, tests, and public issues. Distinguish documented behavior, inspected code, and behavior actually executed in this session.
- **Products and services:** separate advertised claims from demonstrated or independently measured capabilities.
- **Videos and presentations:** use accessible footage, transcripts, or slides. State the material actually reviewed; do not imply that an inaccessible video was watched.

For every consequential claim, retain:

| Field | What to record |
|---|---|
| Claim | The precise fact or interpretation being supported |
| Evidence type | Official requirement, observed result, reported result, user statement, or AI inference |
| Source | Original URL or file, plus page, section, or timestamp where available |
| Timing | Publication or revision date, event or measurement period, and date checked |
| Applicability | Relevant population, geography, environment, and conditions |
| Limitations | What the source cannot establish |
| Counterevidence | Conflicting findings or alternative explanations |

Keep numerical units and denominators intact. Do not generalize a narrow sample to an entire market or compare incompatible measures without explanation. Preserve original quotations and label translations or interpretations.

Use the source appropriate to the claim: organizer materials establish official rules, published work and original data support technical or empirical claims, and participant accounts describe their own experiences. A project's own marketing does not independently verify its effectiveness.

Corroborate important claims where possible. Multiple articles repeating one press release count as one underlying source. If only one source exists, state that limitation. Lack of accessible evidence does not prove that no prior solution, winner, or study exists.

## 4. Analyze Winning Entries and Comparable Work

For each relevant winner, compare:

| Dimension | Evidence to seek |
|---|---|
| Problem framing | Target group, situation, and problem addressed |
| Differentiation | How the entry differed from available approaches at the time |
| Implementation | Idea, prototype, working product, or deployed system, with supporting artifacts |
| Validation | Demo, experiment, user study, or operational evidence and its limitations |
| Communication | How the presentation or report supported its value proposition |
| Published judging | What judges explicitly praised or criticized, if available |
| Subsequent development | Later deployment, commercialization, discontinuation, or unknown status |

Verify awards against organizer records where possible. Mark team self-reports that cannot be corroborated. Do not infer unpublished scores or reasons for winning from the presence of a technology or feature.

Separate observations about winners from causal interpretations. Historical success does not establish suitability for a new track or changed criteria. Identify approaches that were distinctive at the time but have since become commonplace.

Compare current domestic and international alternatives on the dimensions relevant to the competition. If unsuccessful or non-winning entries are available, use them where informative to examine simplistic winner-only explanations; do not invent missing comparisons.

## 5. Seek Counterevidence and Test Applicability

For a promising problem area or apparently strong claim, deliberately investigate:

- Whether existing solutions already address the problem adequately.
- Whether the need is observed in user evidence or merely assumed by a creator.
- Why comparable attempts failed, stalled, or were rejected, when such evidence exists.
- Whether reported performance depends on a narrow dataset or unrealistic conditions.
- Whether the project can actually access the necessary data and execution environment.
- Whether overseas or historical findings apply to the competition's target users and present conditions.

Adapt depth to the track. For ideathons, emphasize evidence of the problem and feasibility of proposed approaches. For AI development, examine data availability, measurement design, and technical limitations. For security challenges, examine the task's threat model, target environment, authorized scope, and validation requirements. Research does not authorize testing external targets.

Treat disagreements as research questions. Compare primary sources, dates, definitions, populations, and measurement conditions. If the conflict remains unresolved, explain how it limits later decisions.

## 6. Repeat Research Based on Gaps and Contradictions

After each substantive research pass, update the map and choose the next action according to its effect on understanding the competition:

1. Missing answers to important questions: change search terms, language, source type, or follow a new evidence trail.
2. Conflicting evidence: inspect original data, timing, and applicability.
3. Important claims resting on one source: seek independent corroboration or document the limitation.
4. New findings that change the assessment: revisit affected research areas and update conclusions.
5. Repeated findings that add little: shift effort to remaining consequential gaps.

Do not ask for approval after each search. Provide concise progress updates and incorporate user corrections. Escalate only decisions that require the user's knowledge or change agreed scope or limits.

Stop and present a research handoff when:

- Mandatory official conditions and judging criteria are established, or their absence or ambiguity is explicitly documented from the official materials.
- Each consequential research area has supporting evidence or an explicit, investigated gap.
- Important contradictions have been resolved or their unresolved implications are explained.
- Further research is producing little information that changes the substantive understanding of the competition.

Evaluate these conditions alongside the agreed execution limits. Reaching a time limit is not proof of completion. If a limit is reached first, report partial coverage and remaining questions. Unresolved mandatory requirements must remain unresolved in subsequent eligibility or readiness decisions.

Do not use a fixed search count, a large link total, or an AI-generated completion percentage as evidence that research is sufficient. Record why stopping is justified and what new information would warrant reopening the investigation.

## 7. Explain the Findings Before Proposing Ideas

Provide Korean deliverables appropriate to the available evidence:

- A readable overview of the competition's purpose, requirements, and competitive context.
- A table of official conditions and judging criteria with direct sources.
- Comparisons of relevant past winners and domestic and international alternatives.
- Evidence for the underlying problems, including counterevidence and limitations.
- Unresolved needs and opportunity areas, framed as problems or questions rather than concrete solution proposals.
- Sources, coverage boundaries, unresolved questions, and potentially useful follow-up research.

Link claims to evidence near the point of use; a source list alone is insufficient. Keep the summary accessible while making detailed evidence available for deeper reading. Follow existing project documentation conventions and avoid duplicating the same evidence across files.

Do not introduce concrete AI-generated product concepts or rank new AI-generated solution candidates in this initial research handoff. First ask the user what problems resonate with them, what they have experienced, and what ideas they want to explore. If those thoughts are already available, summarize them and ask only about missing essentials. After understanding the user's perspective, proceed to evidence-based idea assessment under the main skill.
