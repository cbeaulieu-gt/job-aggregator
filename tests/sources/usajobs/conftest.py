"""Pytest configuration for usajobs integration tests.

Loads .env credentials before the test session so that cassette
recording works with real credentials in local development.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Load .env from the worktree root before the session begins.

    Uses python-dotenv (a dev dependency) to populate environment
    variables needed for cassette recording.  If dotenv is unavailable
    or the .env file is absent, the function is a no-op — cassette
    replay does not need real credentials.

    Args:
        config: The pytest configuration object (unused directly).
    """
    try:
        from dotenv import load_dotenv

        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
    except ImportError:
        pass
