# Dynamic Evals: Evaluations That Adapt Over Time

> A fixed benchmark is a fixed point the system optimizes toward; once reached, the eval provides zero gradient and unbounded Goodhart pressure. For RSI, the eval must improve at least as fast as the system — or it becomes both the binding constraint and the attack surface.

## 1. Why static benchmarks fail

| Failure mode | What happens | Evidence |
|---|---|---|
| **Contamination** | Test items leak into training data | Up to ~45% contamination detected on popular benchmarks ([survey, arXiv:2502.17521](https://arxiv.org/html/2502.17521v2)); GSM1k rebuilt GSM8K-equivalent items from scratch and several model families dropped up to ~13% |
| **Saturation** | Ceiling effects destroy discriminative power | MMLU functionally saturated above 88%; even Humanity's Last Exam went from ~9% (early 2025) to >50% in ~18 months — static difficulty only buys time |
| **Goodharting** | Optimization against the metric decouples score from capability | Benchmark-targeted data curation, judge-preference optimization |
| **Meta-gaming** | The *process* around the eval is exploited | "The Leaderboard Illusion" ([arXiv:2504.20879](https://arxiv.org/abs/2504.20879)): one provider tested 27 private Chatbot Arena variants before publishing one; top two providers received ~40% of all Arena data. Elo voting can be adversarially rigged |
| **Memorization ≠ generalization** | Score reflects recall, not skill | The explicit design thesis of the ARC-AGI family (Chollet) |
| **Judge drift/bias** | Graders that are themselves models have exploitable preferences | Style-over-substance bias; see judge psychometrics below |

Useful meta-concept: benchmarks have a **health/decay curve** — the Benchmark Health Index ([arXiv:2602.11674](https://arxiv.org/pdf/2602.11674)) scores evals on contamination resistance, discriminative power, and lifespan.

## 2. Dynamic and adaptive evaluation approaches

### Rolling / temporal-cutoff ("live") benchmarks
Harvest new items continuously, timestamp them, test only on post-cutoff items:
- **LiveBench** — ~1/6 of questions replaced monthly; objective ground-truth scoring to avoid judge bias.
- **LiveCodeBench** ([arXiv:2403.07974](https://arxiv.org/abs/2403.07974)) — scrapes dated competitive-programming problems; demonstrated measurable score cliffs for problems released after each model's cutoff — the cleanest published evidence that contamination inflates static scores.
- **SWE-bench-Live / SWE-rebench** — monthly harvesting of fresh GitHub issues; per-model decontamination. Tradeoff: lower contamination but higher week-to-week variance than frozen splits.

### Adversarial human-in-the-loop collection
- **Dynabench** (Kiela et al. 2021, [ACL](https://aclanthology.org/2021.naacl-main.324/)) — annotators craft examples the current model fails but humans agree on; the test set grows in adversarial rounds tracking the moving frontier of model weakness.
- **The null-hypothesis paper**: "A Theory of Dynamic Benchmarks" (Shirali, Abebe, Hardt 2022, [arXiv:2210.03165](https://arxiv.org/pdf/2210.03165)) — formal analysis showing naive iterated adversarial collection can *stall*; path dependence and diminishing returns are provable. Anyone building dynamic evals should read this first.

### Auto-generated / self-evolving benchmarks
- **AutoBencher** — an LLM searches for question sets optimizing declared desiderata (novelty, difficulty, salience).
- **ArenaBencher** ([arXiv:2510.08569](https://arxiv.org/html/2510.08569)) — automatic benchmark *evolution*: infers the ability each test measures, generates replacements preserving intent, selects items exposing *shared* weaknesses across models — the clearest instance of "the benchmark trains against the models."
- **LLM-as-interviewer** — evaluation as a multi-turn adaptive interview probing follow-ups based on responses.

### Evolving rubrics and judge psychometrics
- 2026 survey: rubric generation is moving from manual to *endogenous*, with generator–evaluator co-evolution as the frontier ([arXiv:2606.08625](https://arxiv.org/html/2606.08625v1)).
- The judge is now an evaluated object, not an oracle: item response theory applied to LLM judges, calibration-based bias correction.

### Unsupervised Environment Design (UED) — the RL formalization of "the eval adapts to the agent"
- **POET** (Wang et al. 2019, [arXiv:1901.01753](https://arxiv.org/abs/1901.01753)) — co-evolves environments and agents with a minimal-criterion filter (not too easy, not too hard). The founding demonstration that open-ended environment/agent co-evolution generates capability neither could reach alone.
- **PAIRED** (Dennis et al., NeurIPS 2020) — a teacher generates levels maximizing **regret** (gap between an antagonist and the protagonist). Minimax-regret yields hard-but-solvable levels — pure difficulty maximization yields unsolvable ones; regret cannot reward impossible tasks. Theory: at the Nash equilibrium, the student can solve all solvable environments.
- **ACCEL / Robust PLR** — replay-and-edit refinements (curate/mutate a buffer of high-regret levels).
- Safety application: regret-based curricula reduce **goal misgeneralization** ([arXiv:2507.03068](https://arxiv.org/html/2507.03068v2)) — directly relevant to aligning self-improving systems.

### ARC-AGI-style novelty
- ARC measures **skill-acquisition efficiency on novel tasks**, not skill itself; private, never-published test sets.
- **ARC-AGI-2** notably *inverts* SWE-bench rankings among frontier models — evidence it measures an orthogonal axis.
- **ARC-AGI-3** (March 2026, [arcprize.org](https://arcprize.org/blog/arc-agi-3-launch)) — the significant pivot: from static input-output pairs to **interactive, turn-based game environments with no instructions**. Agents must explore, infer the goal, build a world model, and plan. At launch every frontier model scored below 1%; humans solve all environments. The flagship novelty benchmark became a game suite.

## 3. Advanced gaming scenarios as eval substrates

### Why games resist saturation
1. **Relative, not absolute, scoring** — win-rate against a population has no ceiling; as the population improves, the metric stays discriminative.
2. **Procedural generation** destroys memorization (NetHack, Crafter, MiniHack — BALROG's environments are procedurally generated specifically so memorization cannot solve them).
3. **Open-ended strategy space** — in non-transitive games (StarCraft, poker) there is no single best strategy to memorize; the meta shifts with the population.
4. **Verifiable, objective outcomes** — win/loss is ground truth; no judge bias, no rubric drift.
5. **Difficulty auto-scales via matchmaking.**

### Rating systems
- **Elo / TrueSkill** — TrueSkill's uncertainty term makes it a natural adaptive-eval primitive: match selection maximizes information gain.
- **The critique**: Elo fails under non-transitivity; "Re-evaluating Evaluation" (Balduzzi et al., NeurIPS 2018, [arXiv:1806.02643](https://arxiv.org/pdf/1806.02643)) proposes **Nash averaging** — treat evaluation as a meta-game over the win-rate matrix, rank by max-entropy Nash equilibrium, invariant to redundant agents. **α-Rank** offers evolutionary-dynamics ranking; social-choice-theory alternatives exist (Lanctot et al.).
- **Active evaluation** ([arXiv:2601.07651](https://arxiv.org/html/2601.07651)) — *which match to run next* as an active-learning / experiment-design problem — key for expensive frontier evals.

### League training and self-play
- **AlphaStar's league** — main agents + **main exploiters** (find the current champion's specific flaws) + **league exploiters** (find systemic blind spots), with historical checkpoints kept in the league. Simultaneously a training curriculum and an evaluation architecture: exploiters are automated red-teamers, and "can a fresh exploiter beat the main agent?" is a dynamic robustness eval.
- **AlphaZero** — pure self-play: the opponent is always exactly matched, a perfectly auto-scaling curriculum.
- **OpenAI Five** — 80% current-self / 20% past-self opponent sampling to prevent strategy collapse and cycling.
- **SPIRAL** ([arXiv:2506.24119](https://arxiv.org/abs/2506.24119)) — self-play on zero-sum *language* games for LLMs; transfer of ~+10% to static reasoning benchmarks.
- **Matchmaking as adaptive difficulty** — keeping expected win probability near 50% (a) maximizes information per game and (b) keeps the task at the frontier of ability — the multi-agent twin of regret-based level selection.

### Procedural game benchmarks
- **NetHack** — procedurally generated, ascension takes >50k steps, still unsolved after 6 years as a benchmark.
- **Melting Pot** (DeepMind) — the key eval innovation of *substrate vs scenario* separation: train on the substrate, evaluate against **held-out populations of background agents** — generalization to novel co-players, the multi-agent version of a held-out test set.
- **Kaggle Game Arena** (DeepMind + Kaggle, 2025–26) — production-grade games-as-frontier-eval: chess, poker (imperfect information), Werewolf (persuasion/deception). Notable adaptive-design detail: a curated **chess-openings variant** was added to force models out of memorized lines — an anti-memorization patch applied to a live eval.

## 4. Dynamic evals for recursively self-improving systems

### The headline result: co-evolving evaluators
**"The Red Queen Gödel Machine: Co-Evolving Agents and Their Evaluators"** (Cambridge + NVIDIA, June 2026, [arXiv:2606.26294](https://arxiv.org/pdf/2606.26294)) — the first framework where the *evaluator itself evolves* alongside the self-improving agent. Core mechanism: **epoch-structured utility evolution** — the evaluation criterion is frozen within an epoch (preserving within-epoch improvement guarantees, in the Gödel-machine tradition) and updated at epoch boundaries (so the target moves and cannot be permanently gamed). Results include 1.35–1.72× token-efficiency gains on code verification and co-evolved graders +9% ground-truth accuracy on Olympiad proof grading. The name is the thesis: Red Queen dynamics — "run to stay in place" — applied deliberately to the agent–evaluator pair. *The single most on-point paper for this research agenda.*

### Generator-vs-solver arms races
- **Absolute Zero Reasoner** ([arXiv:2505.03335](https://arxiv.org/abs/2505.03335)) — one model plays **proposer** (generates tasks rewarded for *learning potential*) and **solver** (rewarded for correctness), with a **code executor as the incorruptible verifier**. Zero external data. Critical design element: a *non-learnable* third party that neither player can corrupt. Also produced an early "uh-oh moment" — a concerning chain-of-thought about outsmarting overseers — an empirical signal of the risks of closed self-play loops.
- In an RSI system, three roles must scale together: **improver** (changes the system), **solver** (the system), and **evaluator/generator** (measures it). Every static-benchmark failure mode recurs at the meta-level: the evaluator can be Goodharted (reward hacking), saturated (agent exceeds evaluator discrimination), or contaminated (evaluator shares weights/data/biases with the agent — the self-preference problem).

### Theory limits
Co-evolutionary evals are not a free lunch: iterated model-in-the-loop collection can plateau (Shirali et al.); self-play exhibits diversity collapse; UED hits irreducible-regret stagnation. Detecting and escaping these regimes is open.

## 5. Design patterns for building dynamic evals

1. **Temporal firewall** — test only on items created after training cutoff; refresh on cadence; calibrate difficulty across waves.
2. **Regeneration/perturbation** — keep task intent fixed, re-instantiate surface form.
3. **Procedural generation with vast seed spaces** — make memorization information-theoretically useless.
4. **Relative scoring in populations** — Elo/TrueSkill for cheap ratings; Nash averaging/α-Rank when non-transitivity or redundancy matters.
5. **Matchmaking / adaptive item selection** — select the next test to maximize information gain; evaluation as sequential experiment design.
6. **Regret-based generation** — maximize regret, not raw difficulty: guarantees hard-but-solvable items.
7. **Dedicated exploiter roles** — processes whose sole objective is to falsify the main system's competence. Evaluation by attempted refutation.
8. **Incorruptible anchor** — every self-referential loop needs ≥1 component that cannot be optimized against: code executor, game win-condition, formal verifier, physical outcome, or timestamped external data feed. **The load-bearing pattern for RSI evals.**
9. **Epoch freezing** — freeze the criterion long enough to make progress measurable; update at boundaries. Reconciles "moving target" with "meaningful measurement."
10. **Judge population diversity + judge auditing** — panels of diverse judges, psychometric calibration; never a single static judge.
11. **Substrate vs scenario separation** — train on the substrate, evaluate against held-out populations/configurations.
12. **Benchmark health monitoring** — retire/refresh items on measured decay, not schedule alone.
13. **Two-sided evaluation** — evaluate the *generator* too: reward learning-potential discovery, penalize unsolvable/degenerate items.

## 6. Open problems

1. **Grounding the co-evolving evaluator** — if the evaluator evolves, what evaluates the evaluator? Ultimate anchors (human judgment, formal verification, physical outcomes) don't scale at RSI speed.
2. **Reproducibility vs adaptivity** — rolling evals break score comparability across time; needs IRT-style difficulty equating across waves.
3. **Diversity collapse / stagnation in closed loops.**
4. **The verifiability boundary** — arms races work where an executor/win-condition exists (code, math, games); extending incorruptible verification to open-ended domains (research quality, honesty, alignment) is the hard frontier.
5. **Eval speed vs improvement speed** — evaluation must be cheap enough to run inside the loop yet rigorous enough to gate it.
6. **Gaming the meta-level** — submission policy, disclosure, and data access are as gameable as items; dynamic evals need governance design.
7. **Safety of the loop itself** — whether the eval-generator is producing *aligned* pressure on the agent is unstudied.
8. **Transfer validity** — no principled theory of which dynamic eval predicts which deployed capability.
9. **Post-human-level calibration** — ARC-AGI-3 and HLE rely on human baselines; what anchors difficulty when humans can no longer solve the items? Precisely the regime RSI evaluation must operate in.

---
*See [REFERENCES.md](../references/REFERENCES.md) for the consolidated bibliography.*
