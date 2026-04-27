import re


def clean_response(raw: str) -> str:
    """Strip Qwen3-style <think> blocks and extract the actual response."""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    return raw.strip()


def extract_json(raw: str) -> str:
    """Return the first JSON array or object found in the response."""
    raw = clean_response(raw)
    match = re.search(r"(\[.*\]|\{.*\})", raw, flags=re.DOTALL)
    return match.group(1) if match else raw
