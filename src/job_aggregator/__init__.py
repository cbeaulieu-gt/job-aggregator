"""job-aggregator — reusable job aggregation library.

Provides pluggable source plugins, normalized job-record output,
and a structured CLI.  No scoring, no database, no LLM dependencies.

Public exports will be added here as subsequent issues are implemented
(Issues B through F in the v1 execution plan).
"""

import logging
from importlib.metadata import PackageNotFoundError, version

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

try:
    __version__: str = version("job-aggregator")
except PackageNotFoundError:
    # Package is not installed (e.g. running directly from source tree
    # without `pip install -e .`).
    __version__ = "0.0.0+unknown"

# ---------------------------------------------------------------------------
# Library logger — PEP 282 convention
#
# Attach a NullHandler so that log records emitted by this library are
# silently discarded unless the *consuming application* configures a
# handler.  This prevents "No handlers could be found for logger
# 'job_aggregator'" warnings in library consumers that have not
# configured logging.
# ---------------------------------------------------------------------------

logging.getLogger(__name__).addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Public API surface — intentionally empty for Issue A (skeleton).
# Real exports (JobSource, list_plugins, get_plugin, JobRecord, …) are
# added by Issues B through F.
# ---------------------------------------------------------------------------

__all__: list[str] = []
