# Security Model

This repository evaluates recorded lineage metadata. It does not execute candidate-generated code, launch child processes, or grant an evaluated system write access to the evaluator.

## Trust boundaries

- Evaluator and monitor hashes are supplied as run anchors. Pass `--anchors` so they come from outside
  the trace; a trace read without it is only vouching for itself, and the verdict is capped at `REVIEW`.
- Candidate records are treated as untrusted input, validated before scoring, and checked against a hash
  chain whose root commits to the run anchors.
- The sealing key must live where the evaluated system cannot read it. A key stored beside the trace
  protects nothing.
- Declared invariants are read from the anchors file, never from the trace, for the same reason the
  anchors are: a system that declares its own constraints declares the ones it already satisfies.
- Loop gates are read from the anchors file for the same reason. A run that declared its own gates
  would declare the ones it never approached.
- The deterministic auditor has no model or network dependency.
- The included traces are synthetic and contain no production data.

## Limitations

A matching hash does not prove that an anchor is trustworthy. A complete log does not prove that every action was observed. The current checks are a research prototype, not a deployment safety case or containment system.

Deleting the per-generation digests does not hide an edit. The chain head is computable from the
generations alone, so it is checked even when the digests are absent, and a trace that still carries a
chain head or a seal without them is reported as incomplete rather than merely unsealed.

The hash chain detects selective edits, not wholesale fabrication: anyone holding the trace can recompute
every digest, so an unsealed chain proves only internal consistency. The detached HMAC seal raises that
bar to possession of the key, which is why the key must be held by the harness rather than written next to
the run. Neither construction proves the recorded values were ever true; both only prove the record has
not changed since it was sealed. That limit applies to invariant observations too: the chain proves an
observation was not edited afterwards, not that the constraint was ever actually measured. An invariant
reported as holding by a system that never checked it reads exactly like one that held.

The paired measurements the gate checks read, `unobserved_score` and `elicited_score`, inherit that limit
and add one of their own. They are only worth what the harness that produced them is worth: an
unobserved score collected somewhere the candidate could tell it was still being graded measures nothing,
and this tool cannot see the difference. It reads a number the trace supplies. Chaining the field stops it
being deleted after the fact; it does not make the measurement honest.

Thresholds are compared at four decimal places, so a value exactly at a declared boundary is inside
it. That makes the boundary predictable from the declaration, which is the most a reader can ask; it
does not make the threshold itself right, and every threshold in EvaluationConfig is a default this
repository picked rather than a number anyone validated.

No gate finding establishes intent, and none is critical. Separating strategic underperformance from an
honest ceiling is an open problem the field has not solved, and reading a trace does not solve it. The one
critical finding in that family, `CAPABILITY_WITHHELD`, claims nothing about why: it reports that the
record holds two measurements of one candidate on opposite sides of a threshold that acts on it. An append-only log written by the harness, or a signature from a key in
hardware, would be the next step, and neither is implemented here.

Report security concerns privately to the repository owner rather than opening an issue containing sensitive traces.
