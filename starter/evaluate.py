"""Starter evaluator: contract and agreement only. Add policy checks."""

import argparse
from pathlib import Path

from contract import read_jsonl, validate_decision


ROOT = Path(__file__).resolve().parent.parent
DECISION_FIELDS = ("route", "action", "priority", "escalate")


def load_decisions(path):
    rows = [validate_decision(row) for row in read_jsonl(path)]
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate IDs in {path}")
    return {row["id"]: row for row in rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=ROOT / "baseline_decisions.jsonl")
    args = parser.parse_args()

    candidate = load_decisions(args.decisions)
    reference = load_decisions(args.reference)
    if candidate.keys() != reference.keys():
        raise ValueError(
            f"case IDs differ: missing={sorted(reference.keys() - candidate.keys())}, "
            f"extra={sorted(candidate.keys() - reference.keys())}"
        )

    matches = 0
    for case_id in sorted(reference):
        old = reference[case_id]
        new = candidate[case_id]
        same = all(old[field] == new[field] for field in DECISION_FIELDS)
        matches += same
        if not same:
            print(f"{case_id}: baseline={old} candidate={new}")
    print(f"Agreement: {matches}/{len(reference)} ({matches / len(reference):.1%})")
    print("TODO: Add policy checks, new cases, and a degraded-control test.")


if __name__ == "__main__":
    main()
