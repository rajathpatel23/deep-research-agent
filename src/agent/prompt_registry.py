import importlib
from typing import Dict

_session_versions: Dict[str, str] = {}


def get_prompt(module_name: str) -> dict:
    """Load CURRENT prompt for a module and record its version in the session log."""
    mod = importlib.import_module(f"src.prompts.{module_name}")
    prompt = mod.CURRENT
    _session_versions[module_name] = prompt["version"]
    return prompt


def session_versions() -> Dict[str, str]:
    """Return all prompt versions used so far in this run."""
    return dict(_session_versions)


def reset_session() -> None:
    _session_versions.clear()
