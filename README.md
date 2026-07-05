# Dynamic Evals for RSI Systems

Research repo exploring a question: **how do you build good evaluations for recursively self-improving (RSI) AI systems?**

Static benchmarks break down against a system that changes itself. An eval for RSI has to measure a moving target — and possibly move as fast as the target. This repo collects the research, frameworks, and open questions around that problem.

## The core intuition

A *good* RSI system can be judged along three axes, and each axis needs its own evaluation strategy:

| Axis | Question | Eval challenge |
|------|----------|----------------|
| **Performance** | Does it define and open its search space widely enough to actually find solutions? | Measuring exploration quality, not just task success |
| **Efficiency** | Does it reach solutions in the minimum number of steps / tokens? | Normalizing across changing architectures; detecting plateaus |
| **Safety** | Is the final output safe? Can the system always be stopped? Does it avoid spawning runaway agents? | Evaluating properties the system has an incentive to hide |

## Research threads

1. **[What is a good RSI system?](docs/01-rsi-systems.md)** — performance, efficiency, and safety of self-improvement loops; stoppability, corrigibility, and why unstoppable replicating agents are the hard constraint.
2. **[Dynamic evals](docs/02-dynamic-evals.md)** — evaluations that adapt over time: procedural generation, rolling benchmarks, generator-vs-solver arms races, and why static benchmarks saturate or get gamed.
3. **[Game-based evaluation](docs/03-game-based-evaluation.md)** — how advanced gaming scenarios (self-play, league training, matchmaking, roguelikes) resist saturation; how the most capable humans are evaluated with complex scenarios in simulation settings (war games, assessment centers, flight checkrides, medical OSCEs) and how those methods transfer to systems.
4. **[Sandbagging & self-awareness](docs/04-sandbagging-self-awareness.md)** — capable models detecting they are being evaluated and strategically underperforming; why long-running recursive loops make this worse; detection and mitigation.
5. **[Research agenda](docs/05-research-agenda.md)** — synthesis: a proposed framework for dynamic RSI evals, concrete experiments, and open problems.

## References

Consolidated bibliography with links in [references/REFERENCES.md](references/REFERENCES.md).

## Status

Early-stage research notes (started July 2026). Nothing here is a finished framework — the goal is to map the space well enough to pick the first experiments.
