"""job-aggregator — reusable job aggregation library.

Provides pluggable source plugins, normalized job-record output,
and a structured CLI.  No scoring, no database, no LLM dependencies.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from job_aggregator.base import JobSource
from job_aggregator.errors import (
    CredentialsError,
    JobAggregatorError,
    PluginConflictError,
    SchemaVersionError,
    ScrapeError,
)
from job_aggregator.schema import (
    JobRecord,
    PluginField,
    PluginInfo,
    SearchParams,
)

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
# Public API surface — Issue B exports.
# Remaining exports (list_plugins, get_plugin, make_enabled_sources,
# scrape_description) are added by Issues C through F.
# ---------------------------------------------------------------------------

__all__: list[str] = [
    "CredentialsError",
    "JobAggregatorError",
    "JobRecord",
    "JobSource",
    "PluginConflictError",
    "PluginField",
    "PluginInfo",
    "SchemaVersionError",
    "ScrapeError",
    "SearchParams",
    "__version__",
]
