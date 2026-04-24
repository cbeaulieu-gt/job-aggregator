"""Entry point for the job-aggregator console script.

Wires up argparse sub-commands.  Sub-commands are implemented as
self-contained modules under ``job_aggregator/cli/`` and registered
here with a single ``register(subparsers)`` call per module — making
parallel-PR integration a 2-line diff per new command.

Current sub-commands:
    ``sources`` — list registered plugins as JSON (Issue F / #18).

Planned sub-commands (Issues D, E):
    ``jobs``    — fetch and normalise job listings.
    ``hydrate`` — fetch full descriptions for job records.
"""

from __future__ import annotations

import argparse
import sys

from job_aggregator import __version__
from job_aggregator.cli import sources as _sources_cmd


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser.

    Returns:
        A configured :class:`argparse.ArgumentParser` with all registered
        sub-commands attached.
    """
    parser = argparse.ArgumentParser(
        prog="job-aggregator",
        description="Aggregate job listings from multiple sources.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    # Register each sub-command module here — one line per module.
    _sources_cmd.register(subparsers)

    return parser


def main() -> None:
    """Parse arguments and dispatch to the appropriate sub-command handler.

    Exits with code 2 (argparse default) on bad arguments.  Sub-commands
    set ``args.func`` via :meth:`argparse.ArgumentParser.set_defaults`; if
    no sub-command is given, print help and exit 0.

    Returns:
        None.
    """
    parser = _build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func") or args.func is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
