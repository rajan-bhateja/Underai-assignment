# Starter Implementation

This folder contains the OpenAI Responses API runner, keyword fallback,
Pydantic output contract, and evaluator. The assignment brief is in
[../ASSIGNMENT.md](../ASSIGNMENT.md).

## Run

From the repository root, install the requirements and provide a valid
`OPENAI_API_KEY` in the root `.env` file. Generate decisions and evaluate:

```powershell
python starter/run.py --output results/decisions.jsonl
python starter/run.py --cases tests/additional_cases.jsonl --output results/additional_decisions.jsonl
python starter/evaluate.py --decisions results/decisions.jsonl
```

`run.py` uses the configured OpenAI model with the Pydantic `Decision` schema.
It accepts `--cases` and `--output`. If the API or credentials fail, it logs
the problem and uses `triage.py`; inspect the logged fallback count. Fallback
decisions are not model results.

The heuristic applies ordered keyword rules and currently passes the public and
synthetic fixtures, but it is not a semantic classifier. Paraphrases, negation,
and context outside its phrase groups may still be misclassified. Better
semantic understanding could improve fallback coverage, but must be tested
against policy and adversarial cases.

The evaluator checks the output contract, public policy labels, baseline
agreement, synthetic cases, and a deliberately weakened decision. It writes its
output to `evaluation/evaluation.txt` unless `--report-output` is set.
Run metrics such as token counts and fallback totals are printed to the console
at the end of `run.py`; they are not saved under `results/`.
