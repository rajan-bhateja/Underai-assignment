# UnderAI assignment — The Model Migration

This is a standalone applied AI engineering take-home assignment. Start with
[ASSIGNMENT.md](ASSIGNMENT.md). All inputs needed to attempt it are in this folder;
there is no Harbour service, database, private harness, or required API provider.

## Files

| File | Purpose |
| --- | --- |
| [ASSIGNMENT.md](ASSIGNMENT.md) | Candidate brief, deliverables, and review criteria |
| [policy.md](policy.md) | Rules the ticket assistant must follow |
| [baseline_prompt.md](baseline_prompt.md) | Prompt used by the retiring configuration |
| [cases.jsonl](cases.jsonl) | 15 synthetic public tickets |
| [baseline_decisions.jsonl](baseline_decisions.jsonl) | Frozen retiring decisions for those tickets |
| [starter/](starter/) | Runnable candidate codebase: triage logic, model adapter, CLI, evaluator |

## Run the starter

Python 3.10+; no packages are needed for the offline mode:

```bash
python3 starter/run.py --mode heuristic --output results/decisions.jsonl
python3 starter/evaluate.py --decisions results/decisions.jsonl
```

The heuristic is deliberately incomplete. Candidates should edit or replace it,
then extend the evaluator. The optional API mode is documented in
[starter/README.md](starter/README.md).

The cases and company workflow are fictional. They are provided only to make
the exercise runnable without access to UnderAI's systems or customer data.

The assignment is an adaptation of Deployment.inc's [Open Problem 02 — The
Deprecation Notice](https://github.com/Deployment-inc/Deployment.inc-Hiring-Problems/blob/main/problems/OP-02-the-deprecation-notice.md),
licensed [CC BY 4.0](https://github.com/Deployment-inc/Deployment.inc-Hiring-Problems/blob/main/LICENSE.md).
It keeps the migration and evidence challenge while using a smaller original
scenario and dataset.
