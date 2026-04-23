"""Entry point for the job-aggregator console script.

This module is intentionally minimal for Issue A (skeleton).  It exists
so that the ``job-aggregator`` console script declared in
``pyproject.toml`` can be installed and invoked without error.

Real argparse sub-commands (``jobs``, ``hydrate``, ``sources``) are
wired up in Issues D, E, and F of the v1 execution plan.
"""

import sys

from job_aggregator import __version__


def main() -> None:
    """Print a placeholder banner and exit 0.

    Args:
        None — argument parsing is not implemented in this skeleton.
            Real sub-commands land in Issues D, E, and F.

    Returns:
        None.  Exits the process with code 0.
    """
    print(f"job-aggregator v{__version__} (no commands implemented yet; see issue #3 and onward)")
    sys.exit(0)


if __name__ == "__main__":
    main()
