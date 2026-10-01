# UnderAI Model Migration

This standalone assignment evaluates replacing a support-ticket triage model.
The rules in [policy.md](policy.md) are authoritative; the retiring outputs in
[baseline_decisions.jsonl](baseline_decisions.jsonl) are a comparison reference,
not gold labels. See [ASSIGNMENT.md](ASSIGNMENT.md) for the complete brief.

## Setup

Requires Python 3.10 or newer. From the repository root, create and activate a
virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a local `.env` file in the repository root and replace the example value
with your valid OpenAI API key:

```powershell
OPENAI_API_KEY=your_actual_api_key
```

## Generate Decisions

Run the OpenAI Responses API classifier on the 15 public cases:

```powershell
python starter/run.py --output results/decisions.jsonl
```

The runner uses `gpt-5.4-nano` and the structured Pydantic `Decision` schema.
If the API is unavailable or authentication fails, it falls back to the
keyword-based `starter/triage.py` rules. Check the logged `fallback_count`:
fallback results are not model results and can still be wrong. Token totals are
logged only when usage is available for every case; otherwise they are null.

Generate the three synthetic decisions and evaluate both sets:

```powershell
python starter/run.py --cases tests/additional_cases.jsonl --output results/additional_decisions.jsonl
python starter/evaluate.py --decisions results/decisions.jsonl
```

The evaluator checks the output contract, exact baseline agreement, public
policy expectations, synthetic cases, and a deliberately weakened decision.
Its output is saved to `evaluation/evaluation.txt` by default.

The latest recorded model run processed 15 tickets with zero fallbacks: 9,923
input tokens and 476 output tokens (10,399 total). The console timestamps indicate
approximately 24 seconds elapsed. No cost estimate is included because pricing
was not recorded for this run. Run metrics are printed to the console at the end
of each run and are not saved under `results/`.

## Contents

- [cases.jsonl](cases.jsonl): 15 public synthetic tickets.
- [tests/additional_cases.jsonl](tests/additional_cases.jsonl): three synthetic regression cases and expected decisions.
- [starter/candidate_prompt.md](starter/candidate_prompt.md): current model instructions.
- [starter/triage.py](starter/triage.py): keyword-based API fallback. Broader semantic understanding could improve its handling of paraphrases and context.
- [REPORT.md](REPORT.md): measured behavior, disagreements, and comparison.
- [MEMO.md](MEMO.md): rollout recommendation.

All tickets and workflows are fictional. No production data or account actions
are involved.
