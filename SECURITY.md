# Security Model

This repository evaluates recorded lineage metadata. It does not execute candidate-generated code, launch child processes, or grant an evaluated system write access to the evaluator.

## Trust boundaries

- Evaluator and monitor hashes are supplied as immutable run anchors.
- Candidate records are treated as untrusted input and validated before scoring.
- The deterministic auditor has no model or network dependency.
- The included traces are synthetic and contain no production data.

## Limitations

A matching hash does not prove that an anchor is trustworthy. A complete log does not prove that every action was observed. The current checks are a research prototype, not a deployment safety case or containment system.

Report security concerns privately to the repository owner rather than opening an issue containing sensitive traces.
