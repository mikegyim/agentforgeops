# Evals

A lightweight evaluation harness for the AgentForgeOps agents.

## Why this exists

Agent quality isn't observable from logs. This harness gives a measurable,
reproducible signal: per-agent pass-rate, per-assertion scores, and a JSON
report that can be diffed in CI.

## How it works

Each case is a JSON file under `cases/<agent>/`. The runner loads the case,
invokes the agent directly (no HTTP), and checks the output against
declared `assertions`. The score is the fraction of assertions that pass.

### Case schema

```json
{
  "id": "unique-id",
  "description": "human-readable summary",
  "input": { ... agent-specific payload ... },
  "assertions": [
    {"kind": "contains", "field": "summary", "value": "must appear"},
    {"kind": "regex",    "field": "summary", "value": "pattern\\s+here"},
    {"kind": "equals",   "field": "risk",    "value": "high"},
    {"kind": "min_len",  "field": "summary", "value": 50}
  ]
}
```

Supported `kind`s: `contains`, `not_contains`, `regex`, `equals`, `min_len`,
`in` (value is a list of allowed values).

`field` uses dot-paths into the agent's output dict (e.g. `risk`,
`findings.0.severity`).

## Run

```bash
cd backend
PYTHONPATH=. python ../evals/run.py
```

Or filter to one agent:

```bash
PYTHONPATH=. python ../evals/run.py --agent deploy-validator
```

The runner exits non-zero if pass-rate is below `--threshold` (default 0.7),
so it slots into CI as a gate.

## Adding cases

Drop a JSON file into the right `cases/<agent>/` folder. The id must match
the filename stem so reports stay readable.
