import os


def llm_only() -> bool:
    """Return True when the app should avoid deterministic fallbacks and use LLM exclusively."""
    return os.getenv("LLM_ONLY", "false").strip().lower() in {"1", "true", "yes", "on"}

