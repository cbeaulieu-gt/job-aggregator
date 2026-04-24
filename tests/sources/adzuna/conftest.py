"""pytest configuration for adzuna integration tests.

Loads the worktree-root .env file when present so that
--record-mode=once runs pick up real credentials from the environment.
The .env file is gitignored and never committed.

VCR is configured to filter ``app_id`` and ``app_key`` from recorded
request URIs, replacing them with ``FAKE_APP_ID`` / ``FAKE_APP_KEY``.
This ensures cassettes can be replayed without real credentials and that
no secrets leak into committed YAML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


def pytest_configure(config: object) -> None:
    """Load .env from the worktree root before any tests run.

    Args:
        config: The pytest config object (unused directly).
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    env_path = Path(__file__).parents[3] / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    """Configure VCR to scrub Adzuna credentials from recorded requests.

    Replaces the ``app_id`` and ``app_key`` query parameters with
    ``FAKE_APP_ID`` / ``FAKE_APP_KEY`` in both recorded and replayed
    cassettes so that real credentials are never committed to source
    control.

    Returns:
        A dict of VCR configuration options understood by pytest-recording.
    """
    return {
        "filter_query_parameters": [
            ("app_id", "FAKE_APP_ID"),
            ("app_key", "FAKE_APP_KEY"),
        ],
    }
