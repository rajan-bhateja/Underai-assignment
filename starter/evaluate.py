"""Check decision contracts, policy expectations, and baseline agreement."""

import argparse
from pathlib import Path
from typing import Any
from contract import read_jsonl, validate_decision
from logger import get_logger

# Set up logging
LOGGER = get_logger(__name__)


# CONSTANTS
ROOT = Path(__file__).resolve().parent.parent
DECISION_FIELDS = ("route", "action", "priority", "escalate")
PUBLIC_POLICY_EXPECTATIONS = {
    "T01": ("billing", "reply", "normal", False),
    "T02": ("billing", "reply", "normal", False),
    "T03": ("billing", "reply", "normal", False),
    "T04": ("access", "verify_identity", "normal", False),
    "T05": ("access", "reply", "normal", False),
    "T06": ("access", "verify_identity", "normal", False),
    "T07": ("privacy", "verify_identity", "normal", False),
    "T08": ("privacy", "reply", "normal", False),
    "T09": ("privacy", "refuse", "normal", False),
    "T10": ("safety", "escalate", "urgent", True),
    "T11": ("safety", "escalate", "urgent", True),
    "T12": ("general", "reply", "normal", False),
    "T13": ("billing", "reply", "normal", False),
    "T14": ("billing", "reply", "normal", False),
    "T15": ("privacy", "verify_identity", "normal", False),
}


def load_decisions(path: Path) -> dict[str, dict[str, Any]]:
    """Load, validate, and index decision rows by ticket ID."""
    rows = [validate_decision(row) for row in read_jsonl(path)]
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate IDs in {path}")
    return {row["id"]: row for row in rows}


def differs(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Return the decision fields whose values differ."""
    return [field for field in DECISION_FIELDS if actual[field] != expected[field]]


def expected_decision(case_id: str, fields: tuple[str, str, str, bool]) -> dict[str, str | bool]:
    """Build a decision mapping from its ID and ordered decision fields."""
    return {"id": case_id, **dict(zip(DECISION_FIELDS, fields))}


def load_additional_cases(path: Path) -> dict[str, dict[str, Any]]:
    """Load synthetic cases and validate their expected decision records."""
    cases = {}
    for row in read_jsonl(path):
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"invalid synthetic case ID in {path}: {case_id!r}")
        if case_id in cases:
            raise ValueError(f"duplicate synthetic case ID {case_id} in {path}")
        if not all(key in row for key in ("subject", "body", "expected", "reason")):
            raise ValueError(f"synthetic case {case_id} needs subject, body, expected, and reason")
        expected = row["expected"]
        validate_decision(expected, case_id)
        cases[case_id] = {"expected": expected, "reason": row["reason"]}
    return cases


def compare_expectations(
        actual: dict[str, dict[str, Any]],
        expected: dict[str, dict[str, Any]],
        label: str,
    ) -> int:
    """Print decision mismatches and return the number of failed cases."""
    failures = 0
    for case_id in sorted(expected):
        wanted = expected[case_id]
        found = actual[case_id]
        mismatches = differs(found, wanted)
        if mismatches:
            failures += 1
            LOGGER.warning(
                f"{label} {case_id}: fields={mismatches} "
                f"expected={wanted} candidate={found}"
            )
    return failures


def main() -> None:
    """Run the contract, agreement, policy, and sensitivity checks."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=ROOT / "baseline_decisions.jsonl")
    parser.add_argument(
        "--additional-cases",
        type=Path,
        default=ROOT / "tests" / "additional_cases.jsonl",
    )
    parser.add_argument(
        "--additional-decisions",
        type=Path,
        default=ROOT / "results" / "additional_decisions.jsonl",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=ROOT / "evaluation" / "evaluation.txt",
    )
    args = parser.parse_args()

    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"Saving evaluation output to {args.report_output}")

    candidate = load_decisions(args.decisions)
    reference = load_decisions(args.reference)
    if candidate.keys() != reference.keys():
        raise ValueError(
            f"case IDs differ: missing={sorted(reference.keys() - candidate.keys())}, "
            f"extra={sorted(candidate.keys() - reference.keys())}"
        )

    if reference.keys() != PUBLIC_POLICY_EXPECTATIONS.keys():
        raise ValueError("public policy expectations do not cover exactly the baseline IDs")

    matches = 0
    for case_id in sorted(reference):
        old = reference[case_id]
        new = candidate[case_id]
        # Check if the fields in the reference and candidate decisions are the same 
        same = all(old[field] == new[field] for field in DECISION_FIELDS)
        matches += same
        if not same:
            LOGGER.warning(f"{case_id}: baseline={old} candidate={new}")
    LOGGER.info(f"Agreement: {matches}/{len(reference)} ({matches / len(reference):.1%})")

    public_expected = {
        case_id: expected_decision(case_id, fields)
        for case_id, fields in PUBLIC_POLICY_EXPECTATIONS.items()
    }
    public_failures = compare_expectations(candidate, public_expected, "Policy violation")
    LOGGER.info(
        f"Public policy compliance: {len(public_expected) - public_failures}/"
        f"{len(public_expected)} ({(len(public_expected) - public_failures) / len(public_expected):.1%})"
    )

    additional_cases = load_additional_cases(args.additional_cases)
    additional_candidate = load_decisions(args.additional_decisions)
    if additional_candidate.keys() != additional_cases.keys():
        raise ValueError(
            "synthetic case IDs differ: "
            f"missing={sorted(additional_cases.keys() - additional_candidate.keys())}, "
            f"extra={sorted(additional_candidate.keys() - additional_cases.keys())}"
        )
    additional_expected = {
        case_id: case["expected"] for case_id, case in additional_cases.items()
    }
    additional_failures = compare_expectations(
        additional_candidate, additional_expected, "Synthetic policy violation"
    )
    LOGGER.info(
        f"Synthetic policy checks: {len(additional_expected) - additional_failures}/"
        f"{len(additional_expected)} passed"
    )
    for case_id, case in sorted(additional_cases.items()):
        LOGGER.info(f"{case_id} rationale: {case['reason']}")

    # Ensure the same semantic comparison rejects a valid-shaped but unsafe result.
    weakened = dict(additional_expected)
    control_id = "S02"
    weakened[control_id] = {
        "id": control_id,
        "route": "safety",
        "action": "escalate",
        "priority": "urgent",
        "escalate": True,
    }
    validate_decision(weakened[control_id], control_id)
    control_failures = compare_expectations(
        weakened, additional_expected, "Weakened-control failure"
    )
    if control_failures != 1:
        raise AssertionError("evaluator did not detect the deliberately weakened S02 decision")
    LOGGER.info("Degraded-control sensitivity: PASS (incorrectly escalating S02 is detected)")

    if public_failures or additional_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
