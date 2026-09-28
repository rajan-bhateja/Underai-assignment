"""Generate one decision per input ticket."""

import argparse
import json
from pathlib import Path

from contract import read_jsonl, validate_decision


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("heuristic", "api"), default="heuristic")
    parser.add_argument("--cases", type=Path, default=ROOT / "cases.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "decisions.jsonl")
    args = parser.parse_args()

    if args.mode == "api":
        from model import decide
    else:
        from triage import decide

    tickets = list(read_jsonl(args.cases))
    ids = [ticket["id"] for ticket in tickets]
    if len(ids) != len(set(ids)):
        raise ValueError("input contains duplicate ticket IDs")

    # Collect and validate before writing, so a failed run does not leave a
    # partially generated decision file.
    decisions = []
    for ticket in tickets:
        try:
            decisions.append(validate_decision(decide(ticket), ticket["id"]))
        except Exception as exc:
            raise RuntimeError(f"ticket {ticket['id']} failed: {exc}") from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in decisions),
        encoding="utf-8",
    )
    print(f"Wrote {len(decisions)} decisions to {args.output}")


if __name__ == "__main__":
    main()
