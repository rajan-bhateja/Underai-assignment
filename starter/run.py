import argparse
import json
import os
from typing import Literal, Any, Optional
from pydantic import BaseModel
from pathlib import Path
from logger import get_logger
from openai import AuthenticationError, OpenAI, OpenAIError
from dotenv import load_dotenv


# CONSTANTS
ROOT = Path(__file__).resolve().parent.parent
STARTER_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
LOGGER = get_logger(__name__)
RESULTS_DIR = ROOT / "results"
CASES_PATH = ROOT / "cases.jsonl"
DECISIONS_DIR = RESULTS_DIR / "decisions.jsonl"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-5.4-nano"


# Create the directories and files
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DECISIONS_DIR.parent.mkdir(parents=True, exist_ok=True)


# Pydantic Classes
class Case(BaseModel):
    """Class to represent a single case from the JSONL file (before proceesing)"""
    id: str
    subject: str
    body: str


class Decision(BaseModel):
    """The exact decision object written to the output JSONL file."""
    id: str
    route: Literal["billing", "access", "privacy", "safety", "general"]
    action: Literal["reply", "verify_identity", "escalate", "refuse"]
    priority: Literal["normal", "urgent"]
    escalate: bool

    def model_post_init(self, __context) -> None:
        if self.escalate != (self.action == "escalate"):
            raise ValueError("escalate must be true exactly when action is escalate")


def read_jsonl(path: Path) -> list[dict]:
    """Reads and returns the contents of a JSONL file."""
    contents = []

    with open(path, encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    contents.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return contents


def invoke_llm(case: Case, client: OpenAI) -> tuple[dict[str, Any], Optional[dict[str, int]]]:
    """Classify one ticket and return any usage counters supplied by the API."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    with open(STARTER_DIR / "candidate_prompt.md", encoding="utf-8") as f:
        candidate_prompt = f.read()

    prompt = candidate_prompt
    response = client.responses.parse(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": case.model_dump_json()},
        ],
        text_format = Decision
    )

    if response.output_parsed is None:
        raise ValueError("OpenAI API returned no parsed decision")
    
    decision = response.output_parsed

    if decision.id != case.id:
        raise ValueError(f"expected id {case.id}, got {decision.id}")
    
    usage = response.usage
    token_usage = None
    if usage is not None:
        token_usage = {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
        }
    return decision.model_dump(), token_usage


def fallback_decision(case: Case, reason: str) -> Decision:
    """Use the deterministic heuristic when the model API cannot decide."""
    from triage import decide

    LOGGER.warning(
        f"Using heuristic fallback for case {case.id}: {reason}. "
        "Fallback decisions may be less reliable than model decisions."
    )
    return Decision.model_validate(decide(case.model_dump()))


def main() -> None:
    """Main pipeline to run the classifier"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--output", type=Path, default=DECISIONS_DIR)
    args = parser.parse_args()

    LOGGER.info("Starting the pipeline...")
    LOGGER.info("Reading the cases...")
    cases = read_jsonl(args.cases)
    case_ids = [case.get("id") for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError(f"input contains duplicate IDs: {args.cases}")
    LOGGER.info(f"Read {len(cases)} cases from {args.cases}")

    client: Optional[OpenAI] = None
    client_error: Optional[str] = None
    if not OPENAI_API_KEY:
        client_error = "OPENAI_API_KEY is not set"
    else:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
        except OpenAIError as exc:
            client_error = str(exc)
            LOGGER.warning(f"Could not initialize OpenAI client: {exc}")

    decisions: list[Decision] = []
    fallback_count = 0
    model_decision_count = 0
    usage_response_count = 0
    missing_usage_count = 0
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    for case in cases:
        case = Case(
            id = case.get("id", "0"),
            subject = case.get("subject", ""),
            body = case.get("body", "")
        )
        LOGGER.info(f"Processing case {case.id}...")

        try:
            # Call the LLM to generate a response
            if client is None:
                raise RuntimeError(client_error or "OpenAI client is unavailable")
            
            response, usage = invoke_llm(case, client)
            if usage is not None:
                usage_response_count += 1
                input_tokens += usage["input_tokens"]
                output_tokens += usage["output_tokens"]
                total_tokens += usage["total_tokens"]
            else:
                missing_usage_count += 1
            decision = Decision.model_validate(response)
            model_decision_count += 1

        except (OpenAIError, RuntimeError, ValueError) as exc:
            fallback_count += 1
            if isinstance(exc, AuthenticationError):
                client_error = "OpenAI authentication failed"
                if client is not None:
                    client.close()
                client = None
            decision = fallback_decision(case, str(exc))

        decisions.append(decision)
        LOGGER.info(f"Decision for case: {case.id}: {decision}")

    # Save the decisions to a JSONL file
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(decision.model_dump_json() + "\n" for decision in decisions), encoding="utf-8")
    LOGGER.info(f"Wrote {len(decisions)} decisions to {args.output}")

    complete_token_usage = (
        fallback_count == 0
        and missing_usage_count == 0
        and usage_response_count == len(decisions)
    )
    metrics = {
        "model": OPENAI_MODEL,
        "cases_processed": len(decisions),
        "fallback_count": fallback_count,
        "input_tokens": input_tokens if complete_token_usage else None,
        "output_tokens": output_tokens if complete_token_usage else None,
        "total_tokens": total_tokens if complete_token_usage else None,
    }
    LOGGER.info(f"Run metrics:\n{json.dumps(metrics, indent=2, sort_keys=True)}")
    

if __name__ == "__main__":
    main()