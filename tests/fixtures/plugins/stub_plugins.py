"""Stub JobSource plugins for use in orchestrator tests.

Three concrete stubs cover the three ``accepts_query`` values
(``"always"``, ``"partial"``, ``"never"``) so tests can validate
Q4 mixed-mode ``--query`` behaviour without any real HTTP calls.

All stubs accept the same constructor signature used by the orchestrator:
``__init__(credentials, params)`` — but credentials are always ignored and
params are captured for inspection via ``last_params``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar, Literal

from job_aggregator.base import JobSource


def _make_record(
    source: str,
    idx: int,
    *,
    title: str | None = None,
    url: str = "",
    posted_at: str | None = "2026-04-01T00:00:00Z",
) -> dict[str, Any]:
    """Return a minimal normalise()-compatible dict for stub plugins.

    Args:
        source: The SOURCE key of the stub plugin.
        idx: Index used to generate a unique ``source_id``.
        title: Optional title override; defaults to
            ``"Stub Job <source>-<idx>"``.
        url: Optional URL override.
        posted_at: Optional posted_at override.

    Returns:
        A dict conforming to the ``normalise()`` output contract.
    """
    return {
        "source": source,
        "source_id": f"{source}-{idx}",
        "title": title or f"Stub Job {source}-{idx}",
        "url": url or f"https://example.com/{source}/{idx}",
        "posted_at": posted_at,
        "description": f"Description for {source} job {idx}.",
        "description_is_full": False,
        "skip_scrape": False,
    }


class AlwaysQueryPlugin(JobSource):
    """Stub plugin with ``accepts_query="always"`` and two job records.

    No HTTP calls are made.  Yields a single page of two records.
    Records can be inspected via the ``yielded_records`` class variable
    after ``pages()`` is called.

    Attributes:
        last_params: The ``params`` dict passed to the last constructor.
    """

    SOURCE: ClassVar[str] = "stub_always"
    DISPLAY_NAME: ClassVar[str] = "Stub Always"
    DESCRIPTION: ClassVar[str] = "Stub plugin (accepts_query=always)."
    HOME_URL: ClassVar[str] = "https://example.com/always"
    GEO_SCOPE: ClassVar[
        Literal[
            "global",
            "global-by-country",
            "remote-only",
            "federal-us",
            "regional",
            "unknown",
        ]
    ] = "global"
    ACCEPTS_QUERY: ClassVar[Literal["always", "partial", "never"]] = "always"
    ACCEPTS_LOCATION: ClassVar[bool] = True
    ACCEPTS_COUNTRY: ClassVar[bool] = True
    RATE_LIMIT_NOTES: ClassVar[str] = "No limit."
    REQUIRED_SEARCH_FIELDS: ClassVar[tuple[str, ...]] = ()

    #: Captures the most recent params dict for test assertions.
    last_params: dict[str, Any] | None = None

    def __init__(
        self,
        credentials: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the stub; capture params for later inspection.

        Args:
            credentials: Ignored by this stub.
            params: Search parameters dict; stored in ``last_params``.
        """
        AlwaysQueryPlugin.last_params = params or {}

    def settings_schema(self) -> dict[str, Any]:
        """Return empty schema — no credentials needed.

        Returns:
            Empty dict.
        """
        return {}

    def pages(self) -> Iterator[list[dict[str, Any]]]:
        """Yield one page of two stub records.

        Yields:
            A single list containing two normalise()-compatible dicts.
        """
        yield [_make_record(self.SOURCE, 1), _make_record(self.SOURCE, 2)]

    def normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Return raw unchanged — stubs emit pre-normalised dicts.

        Args:
            raw: The dict yielded by ``pages()``.

        Returns:
            The same dict, unchanged.
        """
        return raw


class PartialQueryPlugin(JobSource):
    """Stub plugin with ``accepts_query="partial"`` and one job record.

    No HTTP calls are made.  Yields a single page of one record.

    Attributes:
        last_params: The ``params`` dict passed to the last constructor.
    """

    SOURCE: ClassVar[str] = "stub_partial"
    DISPLAY_NAME: ClassVar[str] = "Stub Partial"
    DESCRIPTION: ClassVar[str] = "Stub plugin (accepts_query=partial)."
    HOME_URL: ClassVar[str] = "https://example.com/partial"
    GEO_SCOPE: ClassVar[
        Literal[
            "global",
            "global-by-country",
            "remote-only",
            "federal-us",
            "regional",
            "unknown",
        ]
    ] = "global"
    ACCEPTS_QUERY: ClassVar[Literal["always", "partial", "never"]] = "partial"
    ACCEPTS_LOCATION: ClassVar[bool] = False
    ACCEPTS_COUNTRY: ClassVar[bool] = False
    RATE_LIMIT_NOTES: ClassVar[str] = "No limit."
    REQUIRED_SEARCH_FIELDS: ClassVar[tuple[str, ...]] = ()

    last_params: dict[str, Any] | None = None

    def __init__(
        self,
        credentials: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the stub; capture params.

        Args:
            credentials: Ignored.
            params: Search parameters dict; stored in ``last_params``.
        """
        PartialQueryPlugin.last_params = params or {}

    def settings_schema(self) -> dict[str, Any]:
        """Return empty schema.

        Returns:
            Empty dict.
        """
        return {}

    def pages(self) -> Iterator[list[dict[str, Any]]]:
        """Yield one page of one stub record.

        Yields:
            A single list containing one normalise()-compatible dict.
        """
        yield [_make_record(self.SOURCE, 1)]

    def normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Return raw unchanged.

        Args:
            raw: The dict yielded by ``pages()``.

        Returns:
            The same dict, unchanged.
        """
        return raw


class NeverQueryPlugin(JobSource):
    """Stub plugin with ``accepts_query="never"`` and one job record.

    No HTTP calls are made.

    Attributes:
        last_params: The ``params`` dict passed to the last constructor.
    """

    SOURCE: ClassVar[str] = "stub_never"
    DISPLAY_NAME: ClassVar[str] = "Stub Never"
    DESCRIPTION: ClassVar[str] = "Stub plugin (accepts_query=never)."
    HOME_URL: ClassVar[str] = "https://example.com/never"
    GEO_SCOPE: ClassVar[
        Literal[
            "global",
            "global-by-country",
            "remote-only",
            "federal-us",
            "regional",
            "unknown",
        ]
    ] = "remote-only"
    ACCEPTS_QUERY: ClassVar[Literal["always", "partial", "never"]] = "never"
    ACCEPTS_LOCATION: ClassVar[bool] = False
    ACCEPTS_COUNTRY: ClassVar[bool] = False
    RATE_LIMIT_NOTES: ClassVar[str] = "No limit."
    REQUIRED_SEARCH_FIELDS: ClassVar[tuple[str, ...]] = ()

    last_params: dict[str, Any] | None = None

    def __init__(
        self,
        credentials: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the stub; capture params.

        Args:
            credentials: Ignored.
            params: Search parameters dict; stored in ``last_params``.
        """
        NeverQueryPlugin.last_params = params or {}

    def settings_schema(self) -> dict[str, Any]:
        """Return empty schema.

        Returns:
            Empty dict.
        """
        return {}

    def pages(self) -> Iterator[list[dict[str, Any]]]:
        """Yield one page of one stub record.

        Yields:
            A single list containing one normalise()-compatible dict.
        """
        yield [_make_record(self.SOURCE, 1)]

    def normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Return raw unchanged.

        Args:
            raw: The dict yielded by ``pages()``.

        Returns:
            The same dict, unchanged.
        """
        return raw


class ErrorPlugin(JobSource):
    """Stub plugin that raises RuntimeError during ``pages()``.

    Used to test ``--strict`` error propagation and default
    continue-on-error behaviour.
    """

    SOURCE: ClassVar[str] = "stub_error"
    DISPLAY_NAME: ClassVar[str] = "Stub Error"
    DESCRIPTION: ClassVar[str] = "Stub plugin that always raises during pages()."
    HOME_URL: ClassVar[str] = "https://example.com/error"
    GEO_SCOPE: ClassVar[
        Literal[
            "global",
            "global-by-country",
            "remote-only",
            "federal-us",
            "regional",
            "unknown",
        ]
    ] = "global"
    ACCEPTS_QUERY: ClassVar[Literal["always", "partial", "never"]] = "always"
    ACCEPTS_LOCATION: ClassVar[bool] = False
    ACCEPTS_COUNTRY: ClassVar[bool] = False
    RATE_LIMIT_NOTES: ClassVar[str] = "No limit."
    REQUIRED_SEARCH_FIELDS: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        credentials: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the stub; no state needed.

        Args:
            credentials: Ignored.
            params: Ignored.
        """

    def settings_schema(self) -> dict[str, Any]:
        """Return empty schema.

        Returns:
            Empty dict.
        """
        return {}

    def pages(self) -> Iterator[list[dict[str, Any]]]:
        """Always raise RuntimeError.

        Raises:
            RuntimeError: Always, simulating a source failure.

        Yields:
            Nothing — raises before yielding.
        """
        raise RuntimeError("Simulated source failure")
        yield  # make mypy happy: this is an iterator

    def normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Return raw unchanged.

        Args:
            raw: Input dict.

        Returns:
            The same dict.
        """
        return raw
