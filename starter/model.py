"""Minimal OpenAI-compatible chat-completions adapter. Replace if needed."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent


def decide(ticket):
    api_key = os.environ.get("UNDERAI_API_KEY")
    base_url = os.environ.get("UNDERAI_BASE_URL")
    model = os.environ.get("UNDERAI_MODEL")
    if not all((api_key, base_url, model)):
        raise RuntimeError("Set UNDERAI_API_KEY, UNDERAI_BASE_URL, and UNDERAI_MODEL")

    prompt = (ROOT / "starter" / "candidate_prompt.md").read_text(encoding="utf-8")
    policy = (ROOT / "policy.md").read_text(encoding="utf-8")
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": prompt + "\n\n" + policy},
            {"role": "user", "content": json.dumps(ticket, ensure_ascii=False)},
        ],
    }
    request = Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)
