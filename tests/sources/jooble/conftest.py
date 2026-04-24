"""Conftest for Jooble integration tests.

Loads the ``.env`` file from the worktree root so that ``JOOBLE_API_KEY``
is available in the environment when the integration test module is imported.
This only applies when running the Jooble tests directly; the key is never
committed to the repo (it is gitignored).

VCR cassette path configuration is set up here.  The API key is scrubbed
from cassette files as a post-recording step (see the ``scripts/`` directory),
not by a ``before_record_request`` hook, because VCR's hook also rewrites the
*outgoing* HTTP request URL — which would cause Jooble to reject the request.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load .env for local recording runs
# ---------------------------------------------------------------------------

# Load .env from the worktree root (four levels up from tests/sources/jooble/).
_WORKTREE_ROOT = Path(__file__).parent.parent.parent.parent
_ENV_FILE = _WORKTREE_ROOT / ".env"

if _ENV_FILE.exists():
    # python-dotenv is a dev dependency; import conditionally so a minimal
    # CI environment (without dotenv) only silently skips loading.
    try:
        from dotenv import load_dotenv

        load_dotenv(_ENV_FILE, override=False)
    except ImportError:
        pass

# ---------------------------------------------------------------------------
# VCR cassette configuration
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, str]:
    """Configure pytest-recording for Jooble integration tests.

    Cassettes are stored in the ``cassettes/`` subdirectory alongside
    this conftest.

    Returns:
        VCR configuration dict consumed by pytest-recording.
    """
    return {
        "cassette_library_dir": str(Path(__file__).parent / "cassettes"),
    }
