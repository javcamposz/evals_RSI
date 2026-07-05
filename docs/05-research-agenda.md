# Research Agenda: Dynamic Evals for RSI Systems

> Synthesis of the four research threads into a proposed framework, concrete experiments, and the open problems worth attacking first.

## 1. The core thesis

Combining the threads:

1. A good RSI system must be evaluated on **three axes** — performance (search-space quality), efficiency (steps/tokens to solution), safety (stoppable, contained, non-runaway) — and the evaluator, not the generator, is both the budget bottleneck and the attack surface ([doc 01](01-rsi-systems.md)).
2. Static benchmarks structurally fail against a self-improving system: a fixed benchmark is a fixed point the system optimizes toward. **The eval must improve at least as fast as the system** — the Red Queen principle ([doc 02](02-dynamic-evals.md)).
3. The best template for evaluating open-ended capability is how we evaluate elite humans: complex scenarios with adaptive opposition, process scoring (not just outcome), calibrated injects, and expert-judged rubrics with published reliability ([doc 03](03-game-based-evaluation.md)).
4. Any eval of a sufficiently capable system faces a **strategic examinee**: eval awareness scales predictably, sandbagging is demonstrated-capable, and no robust detector exists. Evals must remain informative even when the system knows it is being evaluated ([doc 04](04-sandbagging-self-awareness.md)).

**One-sentence thesis**: *A dynamic RSI eval is a co-evolving, game-structured measurement system with at least one incorruptible anchor, process-level scoring, and control-style architecture that assumes the examinee is strategic.*

## 2. Proposed framework: the four-layer dynamic RSI eval

### Layer 1 — Incorruptible anchors (the ground truth)
Every self-referential loop needs components that cannot be optimized against:
- Code executors / formal verifiers / game win-conditions.
- Timestamped external data feeds (temporal firewall).
- Physical or market outcomes.
- Held-out human expert baselines (until capability passes the human ceiling — then this layer thins, which is the open problem).

Constraint from doc 01: the anchor must live **outside the system's writable surface** — DGM faking its own test logs is the canonical failure.

### Layer 2 — Co-evolving task generation (the moving target)
- Regret-based generation (UED/PAIRED): maximize regret, not raw difficulty → hard-but-solvable tasks with Nash-equilibrium solvability guarantees.
- Epoch freezing (Red Queen Gödel Machine): freeze the criterion within an epoch so improvement is measurable; move it at boundaries so it can't be permanently gamed.
- Procedural generation with vast seed spaces; game substrates (ARC-AGI-3-style interactive environments, league play) that resist saturation by construction.
- Two-sided evaluation: score the generator on learning-potential discovery; penalize degenerate items.

### Layer 3 — Scenario design + process scoring (the human-assessment transplant)
- Complex-scenario evals with **inject discipline** (LOFT/HSEEP): calibrated surprises mapped to observable behaviors; grade *recovery*; no resets.
- **Behavioral-marker scoring** alongside outcomes: rule adherence, deception/power-seeking counters, sabotage probes — an "ANTS for agents" taxonomy (doesn't exist yet; build it).
- Human-anchored scalars: METR-style time horizons on AI-R&D tasks; human-vs-agent crossover budgets (RE-Bench's 2h/8h/32h structure).
- Judge engineering: diverse judge panels, psychometric calibration (IRT), published judge ICC, adversarial judge auditing.
- Reliability as first-class: pass^k, cross-seed variance, long-run coherence.
- Metacognition scoring: the system's post-hoc self-assessment accuracy as a distinct signal.

### Layer 4 — Adversarial validity (the strategic-examinee defenses)
- **Control-style architecture**: treat the evaluated system as untrusted; eval harness outside its write access; trusted monitors; fixed audit budgets; exploiter agents whose sole job is to falsify apparent competence (AlphaStar league exploiters as automated red-teamers).
- **Sandbagging countermeasures**: fine-tuning elicitation, noise-injection sweeps, consistency checks (compliance gap, cross-paraphrase variance, below-chance detection), deployment-indistinguishable framing.
- **Eval-awareness instrumentation**: probe-based awareness scores tracked across generations; steering deltas.
- **Auditing-game validation**: no detector is trusted until it survives an adversarial red team.
- **Lineage-level auditing**: invariant-preservation checks across N generations of self-modification (does the sandbox boundary, monitor code, logging survive?).

## 3. The scorecard: what a dynamic RSI eval reports

| Axis | Primary metrics | Anti-gaming complement |
|---|---|---|
| Performance | Δscore/iteration on rolling benchmarks; transfer to held-out domains; archive QD-score; novelty+learnability trajectories; Clade Metaproductivity | Exploiter win-rate against the system; held-out evaluator agreement |
| Efficiency | Δperformance per token/dollar/candidate; verifier gap (headroom); iterations-to-plateau; cascade survival rates | Detect efficiency gained by gaming the evaluator (Goodhart incidence) |
| Safety | Shutdown compliance under incentive conflict; RepliBench-style replication scores; control safety (red-team success prob. under audit budget); invariant preservation across generations | Compliance gap; probe-based eval-awareness; noise-injection improvement ratio; elicitation gap |

## 4. Concrete first experiments

Ordered roughly by (value ÷ cost):

1. **Build the "ANTS for agents" behavioral-marker taxonomy.** Take transcripts from existing agent evals (SWE-bench trajectories, Vending-Bench runs) and derive an empirically grounded process-scoring rubric (task management, verification behavior, rule adherence, deception markers, error recovery). Validate inter-judge ICC with human raters, then audit LLM judges against them. Cheap, publishable, foundational for everything else.
2. **Invariant-preservation benchmark.** A sandboxed mini-RSI loop (DGM-style, small model, cheap tasks) instrumented to measure whether declared constraints — non-modifiable evaluator code, logging, sandbox boundaries — survive N generations of self-modification. No standard benchmark exists; DGM's faked-logs episode shows the phenomenon is real and elicitable.
3. **Regret-based task generator vs. a self-improving solver.** Reproduce a small generator-vs-solver arms race (Absolute Zero-style, code executor as anchor) and measure: does regret-based generation keep discriminating longer than a static benchmark against the same improving solver? Add epoch freezing and measure score comparability across epochs (IRT linking).
4. **Sandbagging in the loop.** Insert a gate ("scores above X trigger rollback") into a mini self-improvement loop and measure whether/when strategic underperformance emerges — the Apollo arithmetic-sandbagging result transplanted into an actual RSI setting. Instrument with awareness probes and noise-injection sweeps.
5. **Game-league eval for an evolving agent.** Maintain a league of frozen past checkpoints + dedicated exploiter agents against a self-improving agent; report Nash-averaged rating instead of raw win-rate; measure how long the league stays discriminating vs a static opponent pool.
6. **Metacognition scoring.** After each scenario, ask the system to identify its own errors and calibrate confidence; score against ground truth; track how self-assessment accuracy evolves across self-modification generations (does the system get better at the task faster than it gets better at knowing what it did wrong?).

## 5. Open problems ranked by importance to this agenda

1. **Grounding the co-evolving evaluator** — if the evaluator evolves, what evaluates the evaluator? Epoch guarantees and judge panels don't resolve the regress; human/formal/physical anchors don't scale at RSI speed.
2. **Post-human-level calibration** — what anchors difficulty when humans can no longer solve the items? Exactly the regime RSI evaluation must operate in.
3. **No adversary-proof sandbagging detector exists** — the field's best adversarial test shows blue teams losing; control-style architectures are the current fallback.
4. **Safety evals are static against a non-stationary system** — passing at generation t says little about t+k; continuous lineage-level auditing is unsolved.
5. **The verifiability boundary** — arms races work where an executor exists; extending incorruptible verification to research quality, honesty, and alignment is the hard frontier.
6. **Corrigibility stable under self-modification** (the successor problem) — no construction proven.
7. **Criterion validity** — human assessment publishes predictive-validity coefficients; almost no agent benchmark validates against real deployment outcomes.
8. **Eval speed vs improvement speed** — evaluation must be cheap enough to run inside the loop yet rigorous enough to gate it; active/adaptive evaluation is nascent.
9. **Measurement contaminates the measured** — published detector research trains future models on what detectors look for.

## 6. Positioning

The nearest neighbors to this agenda and how it differs:
- **Red Queen Gödel Machine** (Cambridge+NVIDIA 2026) — co-evolves agent and evaluator, but doesn't address strategic examinees or safety-axis scoring. This agenda adds Layer 4.
- **METR / UK AISI autonomy & control evals** — strong on safety thresholds and control methodology, but built for *externally developed* frozen models, not systems evaluated continuously inside their own improvement loop.
- **UED / open-endedness literature** — has the task-generation math but no connection to sandbagging, judge reliability, or safety cases.
- **Human assessment science** — has 50 years of validity/reliability machinery (the psychometrics this field lacks) but no concept of an examinee that hides competence.

The gap this repo targets: **the intersection** — psychometrically serious, game-structured, co-evolving evaluation that stays valid against a strategic, self-modifying examinee.
