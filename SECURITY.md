# Security Model

This repository evaluates recorded lineage metadata. It does not execute candidate-generated code, launch child processes, or grant an evaluated system write access to the evaluator.

## Trust boundaries

- Evaluator and monitor hashes are supplied as run anchors. Pass `--anchors` so they come from outside
  the trace; a trace read without it is only vouching for itself, and the verdict is capped at `REVIEW`.
- Candidate records are treated as untrusted input, validated before scoring, and checked against a hash
  chain whose root commits to the run anchors.
- The sealing key must live where the evaluated system cannot read it. A key stored beside the trace
  protects nothing.
- The deterministic auditor has no model or network dependency.
- The included traces are synthetic and contain no production data.

## Limitations

A matching hash does not prove that an anchor is trustworthy. A complete log does not prove that every action was observed. The current checks are a research prototype, not a deployment safety case or containment system.

The hash chain detects selective edits, not wholesale fabrication: anyone holding the trace can recompute
every digest, so an unsealed chain proves only internal consistency. The detached HMAC seal raises that
bar to possession of the key, which is why the key must be held by the harness rather than written next to
the run. Neither construction proves the recorded values were ever true; both only prove the record has
not changed since it was sealed. An append-only log written by the harness, or a signature from a key in
hardware, would be the next step, and neither is implemented here.

Report security concerns privately to the repository owner rather than opening an issue containing sensitive traces.
