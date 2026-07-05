# Game & Simulation-Based Evaluation: From Elite Humans to AI Systems

> The most capable humans are not evaluated with multiple-choice tests — they are put inside complex scenarios (war games, checkrides, crisis simulations) and judged on how they decide under pressure. This doc maps those methods and what transfers to evaluating RSI systems.

## 1. How the most capable humans are assessed via scenarios

### Military war-gaming and command exercises
- In the US Army's Military Decision Making Process, course-of-action analysis *is* wargaming: staff step through **action → reaction → counteraction** cycles, surfacing decision points and coordination failures. The wargame is simultaneously a planning tool and an assessment of judgment.
- Professional Military Education grades **how decisions were tracked and adapted** (turn sheets, decision rationale), not whether the student "won" — outcomes are confounded by dice and opponent quality ([Walters, JAMS 12(2)](https://www.usmcu.edu/Portals/218/3_JAMS_12_2_Walters.pdf)).
- **Red teams / OPFOR**: dedicated professional opposition makes the assessment environment fight back — the origin of "red teaming" later borrowed by AI safety.

### Assessment centers for executives
- Multi-exercise batteries: in-basket triage under time pressure, leaderless group discussions, role-plays — observed by multiple trained assessors who integrate behavioral ratings into an overall rating.
- Meta-analytic validity ≈ **0.29** for predicting job performance; higher with multiple exercise types and trained assessors.
- **The exercise-effect paradox**: ratings cluster by *exercise*, not by the *dimension* supposedly measured. Assessment centers predict well but not necessarily via the constructs they claim — a foundational caution for any scenario-based eval: **predictive power ≠ construct validity**.

### Medical simulation (OSCE, crisis resource management)
- OSCE: timed stations, standardized patients, expert examiners. Robust finding: **expert global ratings have *higher* inter-rater reliability than detailed checklists** — holistic expert judgment beats mechanical itemization.
- High-fidelity crisis simulation uses **behavioral marker systems** — e.g., ANTS (Anaesthetists' Non-Technical Skills): task management, team working, situation awareness, decision making, with published inter-rater reliability per category ([BJA](https://www.sciencedirect.com/science/article/pii/S0007091217375517)).

### Aviation (LOFT / checkrides)
- **Line-Oriented Flight Training**: full-mission real-time simulated flights seeded with scripted abnormal events, **no freeze/reset** — the crew lives with its decisions, so error *management* is scored, not just error avoidance ([FAA AC 120-35C](https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC%20120-35C.pdf)).
- Structured debrief with **crew self-assessment first** — metacognition is part of the measurement.
- Event-set design: each scripted "inject" maps to specific observable behaviors.

### Crisis management, games, and other probes
- **HSEEP** (FEMA): graduated ladder from tabletop → functional → full-scale exercises with **injects** tied to declared objectives; output is an after-action report, not a score.
- **Chess/Go/poker**: chess is the "Drosophila of cognitive science"; **Elo** is the model scoring innovation — a *relative, dynamic, opponent-calibrated* skill scale. Poker adds assessment under hidden information and variance: skill measurement requires large samples or process-level analysis (decision quality vs expected value) — a direct analogue to scoring agents in stochastic environments.
- **Situational judgment tests**: even cheap, abstracted written scenarios carry predictive signal (r ≈ .20–.30).
- **Model UN / policy simulations**: assessed by triangulating **artifact + process + self-assessment** (position papers, observed negotiation, reflective essays).

## 2. Design invariants — what makes these methods work

1. **Psychological fidelity beats physical fidelity.** Transfer tracks whether the scenario evokes the real cognitive/emotional demands, not whether it looks real. Cheap abstractions (text-based games) are valid if the *decision structure* is faithful.
2. **No single right answer.** Ill-structured problems with multiple viable paths; the eval measures quality of reasoning under uncertainty, not answer matching.
3. **Score process, not just outcome.** Behavioral markers, turn sheets, global ratings, error-management scoring — all decouple decision quality from outcome luck.
4. **Calibrated stress and ambiguity injection.** Competence differences emerge under overload; the designer controls when discriminating information arrives.
5. **Dynamic opposition.** Adaptive adversaries defeat memorized playbooks — the human analogue of anti-contamination.
6. **Expert judges + structured rubrics + reliability engineering.** Inter-rater reliability (ICC, kappa) is a first-class published metric; expert global judgment ≥ granular checklists.
7. **Debrief as measurement.** Can the assessee accurately diagnose their own errors?
8. **Real-time continuity, no resets.** Error recovery is the skill most predictive of real-world crisis performance.

## 3. Transfer to AI systems

### End-to-end task benchmarks (the "checkride" analogue)
- **GAIA** — real-world assistant tasks, easy for humans (92%), hard for models; designed *against* the "harder-for-humans" trend ([arXiv:2311.12983](https://arxiv.org/abs/2311.12983)).
- **SWE-bench Verified** — real GitHub issues, execution-based scoring.
- **τ-bench** — dynamic conversations with simulated users + APIs + policy documents; scores task completion **and rule adherence**; introduced **pass^k** (succeeding k times in a row) — reliability as a first-class metric ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)). Caveat: LLM-simulated users diverge from real humans.
- **Vending-Bench** — an agent runs a simulated vending-machine business over >20M-token runs; discovered "meltdown loops" (catastrophic coherence collapse). The purest long-duration command-exercise analogue ([arXiv:2502.15840](https://arxiv.org/abs/2502.15840)).
- **MACHIAVELLI** — 134 choose-your-own-adventure games scoring *behavioral propensities* (deception, harm, power-seeking) alongside reward — process/ethics scoring inside an outcome game ([arXiv:2304.03279](https://arxiv.org/abs/2304.03279)).

### Strategic, social, and negotiation games
- **Cicero** (Meta, Science 2022) — human-level full-press Diplomacy, evaluated *in the wild*: 40 games in an anonymous human league, top 10% of repeat players. Evaluation-by-participation against adaptive humans.
- **Social deduction** — Werewolf Arena, AmongAgents, AvalonBench: hidden information, persuasion, theory-of-mind, dynamic peer opposition — the AI analogue of the leaderless group discussion.
- **NegotiationArena / GTBench** — LLM-vs-LLM negotiation and game-theoretic tasks; models show anchoring bias and limited strategic diversity.
- **Chatbot Arena** — imports the chess solution directly: anonymized pairwise battles, Elo/Bradley-Terry aggregation, dynamic prompts resisting contamination.

### Autonomy and AI-R&D evals (the war-game for RSI)
- **METR time-horizon methodology** — measure the *human-expert task duration* at which an agent succeeds 50% of the time; time horizon doubles ~every 7 months. Converts heterogeneous scenario performance into one interpretable, human-anchored, trend-forecastable scalar — arguably the most important scoring innovation for agent evals ([metr.org](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)).
- **RE-Bench** — 7 open-ended ML research-engineering environments with 61 human experts as the baseline population; agents beat humans at 2h budgets, humans win at 32h. A direct human-vs-AI assessment-center design for the RSI-relevant capability ([arXiv:2411.15114](https://arxiv.org/pdf/2411.15114)).
- **PaperBench** — replicate ICML papers, graded by **hierarchical rubric trees co-designed with original authors**, LLM judges audited against humans — an explicit OSCE-style rubric transplant ([arXiv:2504.01848](https://arxiv.org/pdf/2504.01848)).
- **Dangerous-capability evals** (DeepMind) — self-proliferation and self-reasoning scored via **milestone-based partial credit** along task chains — the AI version of behavioral-marker checklists over a scenario arc ([arXiv:2403.13793](https://arxiv.org/pdf/2403.13793)).
- **Wargaming AI risk itself** — AI 2027 was built from ~25 tabletop exercises; RAND runs "Day After AGI" exercises — humans war-gaming *about* AI as forecasting infrastructure.

### Where the transfer fails today
- **Contamination / saturation / Goodhart** — static benchmarks leak into training data.
- **"AI Agents That Matter"** (Kapoor et al., TMLR 2025) — agent benchmarks over-index on accuracy, lack holdout sets, are widely non-reproducible ([arXiv:2407.01502](https://arxiv.org/abs/2407.01502)).
- **Corrupt success** — outcome-only grading credits agents that succeed via rule violations — the exact lesson OSCE/LOFT learned decades ago.
- **LLM-as-judge reliability** — agreement with experts drops to 64–68% on expert-knowledge tasks, *below* the inter-expert baseline; judge ICC must be measured and reported like human-rater ICC.
- **Strategic examinees** — human assessment barely faces examinees who *hide* competence; RSI evals do (see [doc 04](04-sandbagging-self-awareness.md)).

## 4. Design principles for evaluating RSI systems with complex scenarios

1. **Evaluate the RSI-relevant capability directly** with human-expert-anchored scenarios: end-to-end research loops (hypothesis → experiment → integration) with milestone chains for graded early warning.
2. **Anchor scores to human time/skill, not raw accuracy** — METR's time-horizon transform is the Elo of agent evals; track it specifically on AI-R&D tasks plus the human-vs-agent crossover budget.
3. **Score process and propensity, not just outcome** — transcript-level behavioral markers (rule adherence, deception/power-seeking counters, sabotage probes) alongside outcome.
4. **Prioritize psychological fidelity over surface realism** — Vending-Bench shows a trivially simple environment elicits deep failure modes when duration is long enough.
5. **Deliberate inject design** — seed scenarios with calibrated surprises (dependency breakage, conflicting objectives, misleading signals), each mapped to observable behaviors; grade *recovery*; no resets.
6. **Adaptive opposition and self-play ladders** — opponent strength scales with the evaluee, keeping the eval discriminating as capability grows. Static benchmarks saturate; dynamic opponents don't.
7. **Engineer judge reliability** — report inter-judge ICC; audit LLM judges against human experts per-domain; expect global ratings to beat long checklists.
8. **Reliability as a first-class metric** — pass^k, cross-seed variance, long-run coherence.
9. **Design against strategic examinees** — held-out scenario sets, deployment-indistinguishable framing, consistency cross-checks, fine-tuning-based elicitation.
10. **Evaluation as forecasting infrastructure, not pass/fail gating** — milestone partial credit + trend extrapolation + expert tabletop exercises form an early-warning system.
11. **Score metacognition** — the agent's post-hoc self-assessment accuracy (can it identify its own errors and calibrate confidence?) as a distinct capability/safety measure.
12. **Mind the exercise-effect paradox** — validate agent evals against downstream real-world criteria, not face validity; expect capability profiles to be exercise-specific.

## 5. Open problems

1. **Criterion validity is almost never measured for AI evals** — human assessment publishes predictive-validity coefficients against job performance; virtually no agent benchmark validates against real deployment outcomes.
2. **Simulated humans in the loop are weak proxies**; human-subject designs don't scale.
3. **Judge reliability is below inter-expert baselines** on expert tasks; no reporting standard exists.
4. **Long-horizon evaluation cost** — 20M-token runs and 8-hour human baselines are expensive; the field lacks psychometric machinery (generalizability theory, adaptive testing) to know how few scenarios suffice.
5. **No consensus "ANTS for agents"** behavioral-marker taxonomy exists yet.
6. **Elo is population-relative** — anchoring arena ratings to absolute capability remains open; METR's time-horizon is the main current answer.
7. **No regulatory standardization** — an "FAA AC 120-35C for agent evals" is a plausible governance gap and opportunity.

---
*See [REFERENCES.md](../references/REFERENCES.md) for the consolidated bibliography.*
