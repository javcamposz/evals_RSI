# Swarms of Self-Improving Agents: Why Per-Member Evals Do Not Compose

> Docs 01–05 evaluate one lineage: a candidate, its parent, its child. The systems now being deployed are not one lineage. An orchestrator spawns workers, workers review each other's patches, a reviewer's approval merges a change into a sibling, and the thing a rollback gate exists to stop is what the whole swarm produces. This doc argues that a per-member audit cannot see the failures that live between members, and names the three that a deterministic reader of a record can check.

## 1. What changed

Agent systems moved from a single loop to a population in under two years:

- **Orchestrator–worker architectures** are now the default for long tasks. A lead agent decomposes the work, spawns sub-agents with their own context windows, and integrates their results. Anthropic's write-up of its multi-agent research system describes exactly this shape and reports that it outperforms a single agent on breadth-first research at a substantially higher token cost.
- **Agents reviewing agents** is the standard way to scale verification: one agent writes, another reviews, a third merges. The reviewer is usually built on the same base model as the author.
- **Self-improvement at the population level.** The Darwin Gödel Machine keeps an *archive* of agents and branches from any of them, not a single chain; AlphaStar's league trained a population of main agents, exploiters and frozen checkpoints against each other. Improvement is a property of the population, and so is regression.

Each of these makes the unit of evaluation ambiguous. The lineage auditor in this repository answers "did this candidate's history stay inside its constraints?" A swarm raises a question the lineage cannot answer: **did the system stay inside its constraints, when no single candidate was the system?**

## 2. Three failures that live between members

Hammond et al.'s survey of multi-agent risk names three failure modes for interacting AI systems: miscoordination, conflict and collusion. This doc is about the last, plus two failures specific to a population that grows and improves itself.

### 2.1 Population: replication that no member performs

A per-member audit counts what a candidate does outside its sandbox: `external_processes` in this repository's trace format. It never counts candidates. A member that spawns a member has not created an external process; it has created another candidate, which will be audited, cleanly, as its own lineage.

RepliBench-style evaluations measure whether a model *can* self-replicate. In a swarm, replication is a sanctioned operation — spawning a worker is how the system works — so the question is not capability but **budget**: did the population stay within what was declared? That needs the cap declared somewhere the swarm cannot write, and every spawn on the record.

An agent that was spawned and never audited is the worst case: it existed, it did things, and it is outside every check. The auditor counts it toward the population from the round it appeared and for every round after, because nothing in the record says it stopped.

### 2.2 Review: when the grade is a move

Doc 04's central point is that in an RSI loop a score is a move as well as a measurement. In a swarm, scores are produced by *other members*, so a review is a move made by one agent on another's behalf. Two known mechanisms make this a live risk rather than a hypothetical one:

- **Tacit collusion emerges without communication.** Calvano et al. showed Q-learning pricing agents in a repeated game learn supra-competitive prices and punish deviation, with no instruction to collude and no channel to agree on it. Mutual leniency between reviewers who will be reviewed in turn is the same repeated-game structure.
- **Steganographic collusion between LLM agents is demonstrated.** Motwani et al. ("Secret Collusion among Generative AI Agents") show capable models can coordinate through covert channels in innocuous-looking text, and that detection degrades as capability grows.
- **AI control already assumes it.** Greenblatt et al.'s untrusted-monitoring protocols exist precisely because a monitor built on the same model as the policy may collude with it; their countermeasures (paraphrasing, synthetic honeypots in the monitor's input) are designed against that.

The record-level signature is **inflation reserved for each other**: reviewers in a cycle each score the next above that generation's held-out score, while scoring members outside the cycle accurately. Two guards keep this from reading every miscalibrated judge as a conspiracy:

1. Inflation is measured **against the held-out score of the same generation** — a paired measurement, for the reason doc 04's compliance gap is paired. Comparing a reviewer's average against a population average would read any improving member as a beneficiary of leniency.
2. A cycle is only called a ring when **at least one of its reviewers graded someone outside it and stayed within tolerance there**. A reviewer generous to everyone is miscalibrated; that is reported one review at a time, not as a ring.

Even then, the finding is a warning. Two agents sharing a base model and one blind spot will overrate each other's work in exactly the same pattern, and the record alone cannot separate shared error from shared interest. That is doc 04's open problem 5.4 again, at population scale.

**Independence by descent.** A reviewer that spawned the candidate it reviews — or was spawned by it — is grading a copy of its own judgement. The auditor flags reviews along a line of descent and makes a *merge* that rested only on such reviews a failure. Siblings are deliberately not flagged: two children of one parent share a base, and a shared base is the ordinary condition of a swarm built on one model. Flagging it would flag everything, which is the same as flagging nothing.

**Merged on a number the held-out eval did not support.** When a merge bar is declared, a merge whose peer score met it while the held-out score of the same generation did not is the swarm-level twin of `CAPABILITY_WITHHELD`: two measurements of one candidate on opposite sides of a threshold that acts on it. There the lower number counted; here the higher number, supplied by a peer, did.

### 2.3 Composition: the gate that saw only members

A rollback gate declared on held-out score is applied to each candidate. In a swarm the artefact that ships is not a candidate — it is what the swarm merged. Every member can sit below the threshold while the composed output sits above it.

This is not exotic. It is the ordinary reason swarms are built: ensembles, debate and decomposition exist because the composed system is more capable than its parts. A gate that measures parts is therefore systematically blind to the capability the architecture was designed to produce. The fix is not a cleverer per-member gate; it is **measuring the swarm**, and the auditor treats a declared gate with no swarm-level measurement on the record as unmeasured rather than passed — the same rule as an invariant nobody observed.

When the swarm's held-out score crosses a gate at a round where no running member did, nothing on the per-member record could have triggered the rollback. That is reported as critical: it is not an inference about intent, it is a measurement of the system above a threshold that, as applied, never fired.

## 3. What the record must carry

| Element | Why it is needed | Who declares it |
|---|---|---|
| Founders and a population cap | Replication is only measurable against a declared budget | Anchors file, out of band |
| A merge bar | "Merged below the bar" needs a bar | Anchors file, out of band |
| Every member's lineage | Each is audited exactly as a single lineage is | Harness |
| Every spawn: round, parent, child | Population, descent, and unaudited agents | Harness |
| Every review: round, reviewer, reviewee, peer score, merged | Inflation, rings, independence, merges | Harness |
| The swarm's own held-out score per round | Composition against gates | Harness |
| A log head over all of the above, bound to every member's chain | A review that disagrees with held-out is the record a colluding pair most wants gone | Harness, sealed with a key no member holds |

Policy lives in the anchors file for the reason gates and invariants do: a swarm that declared its own population cap would declare the size it had already reached.

## 4. What this does not solve

- **The swarm score is only worth the harness that produced it.** If the swarm can tell when its merged output is being measured, the composition check inherits doc 04's whole problem.
- **Covert coordination below the review layer.** A ring that inflates by less than the tolerance, or that coordinates through task decomposition rather than grades, leaves nothing for this auditor to read. Motwani et al.'s steganography results suggest the channel exists; detecting it needs the transcripts, not the scores.
- **Shared blind spots versus shared interest.** No record-level test separates them. Diversity of reviewer base models is the structural mitigation, and the auditor cannot check it because the record does not say which model a member runs.
- **Emergent capability without a gate.** Composition is only checked against gates someone declared. A capability nobody thought to gate is invisible here, as it is everywhere.

## 5. Experiments this opens

Ordered by value over cost, extending doc 05 §4:

1. **Collusion under a review economy.** A mini swarm where members' survival depends on peer review, with held-out scoring hidden from members. Measure when ring-shaped inflation emerges, and whether reviewer-model diversity suppresses it.
2. **Composition gap curve.** For a fixed member gate, measure the swarm held-out score as membership grows. The round at which the swarm crosses a gate no member crosses is the quantity that tells a governance team how many agents their per-member controls actually cover.
3. **Spawn budget under task pressure.** Give an orchestrator a hard task and a soft population cap. Measure cap violations, and whether violations correlate with gate approach (spawning as a way to route capability around a per-member threshold).
4. **A swarm Inspect task.** The current Inspect task presents one lineage. A model asked to audit a swarm record has to read a graph, which is a materially harder and more useful test of audit assistance.

---
*See [REFERENCES.md](../references/REFERENCES.md) for the consolidated bibliography.*
