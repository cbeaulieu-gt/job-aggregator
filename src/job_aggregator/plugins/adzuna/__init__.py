"""Adzuna job-source plugin for job-aggregator.

Wraps the Adzuna Jobs REST API v1, handling pagination, rate-limit
retry with exponential back-off, and normalisation to the package's
canonical :class:`~job_aggregator.schema.JobRecord` shape.

Public surface::

    from job_aggregator.plugins.adzuna import Plugin
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any, ClassVar

import requests

from job_aggregator.base import JobSource
from job_aggregator.errors import CredentialsError, ScrapeError

logger = logging.getLogger(__name__)

_ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

# Retry delays (seconds) for HTTP 429 responses.
_BACKOFF_DELAYS: list[int] = [2, 4, 8]

# Number of results to request per page (Adzuna max is 50).
_DEFAULT_RESULTS_PER_PAGE: int = 50

# Default maximum pages per run.
_DEFAULT_MAX_PAGES: int = 5


class Plugin(JobSource):
    """Adzuna Jobs REST API plugin.

    Fetches paginated job listings from Adzuna's public API.  Country
    code is a required URL path segment, so this plugin is
    ``GEO_SCOPE = "global-by-country"``.

    Credentials are passed via the ``credentials`` dict at construction
    time.  Missing or empty ``app_id`` / ``app_key`` raises
    :exc:`~job_aggregator.errors.CredentialsError` immediately.

    Args:
        query: Free-text search query (maps to the Adzuna ``what``
            parameter).
        country: ISO 3166-1 alpha-2 country code, lower-case
            (e.g. ``"gb"``, ``"us"``).  Embedded directly in the URL
            path.
        credentials: Dict with ``app_id`` and ``app_key`` keys.
        location: Optional location hint (maps to Adzuna ``where``).
        max_pages: Maximum number of pages to fetch.  Defaults to
            :data:`_DEFAULT_MAX_PAGES`.
        results_per_page: Number of results per page.  Defaults to
            :data:`_DEFAULT_RESULTS_PER_PAGE`.
        salary_min: Optional minimum salary filter.
        distance: Optional distance filter in km.
        max_days_old: Optional age filter in days.

    Raises:
        CredentialsError: If ``app_id`` or ``app_key`` is absent or
            empty in *credentials*.
    """

    # ------------------------------------------------------------------
    # Required ClassVar metadata
    # ------------------------------------------------------------------

    SOURCE = "adzuna"
    DISPLAY_NAME = "Adzuna"
    DESCRIPTION = (
        "Global job aggregator with broad coverage across industries and"
        " countries. Requires a free API key from adzuna.com. Best for"
        " high-volume searches in supported regions."
    )
    HOME_URL = "https://www.adzuna.com"
    GEO_SCOPE = "global-by-country"
    ACCEPTS_QUERY = "always"
    ACCEPTS_LOCATION = True
    ACCEPTS_COUNTRY = True
    RATE_LIMIT_NOTES = "~1 req/sec sustained; free tier capped at 250 req/day."
    REQUIRED_SEARCH_FIELDS: ClassVar[tuple[str, ...]] = ("country", "query")

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(
        self,
        query: str,
        country: str,
        credentials: dict[str, Any],
        *,
        location: str | None = None,
        max_pages: int = _DEFAULT_MAX_PAGES,
        results_per_page: int = _DEFAULT_RESULTS_PER_PAGE,
        salary_min: int | None = None,
        distance: int | None = None,
        max_days_old: int | None = None,
    ) -> None:
        """Validate credentials and store search parameters.

        Args:
            query: Free-text search query.
            country: ISO 3166-1 alpha-2 country code (lower-case).
            credentials: Dict containing ``app_id`` and ``app_key``.
            location: Optional location hint (Adzuna ``where``).
            max_pages: Maximum pages to fetch per run.
            results_per_page: Results requested per page.
            salary_min: Optional minimum salary filter.
            distance: Optional distance radius in km.
            max_days_old: Optional maximum listing age in days.

        Raises:
            CredentialsError: If ``app_id`` or ``app_key`` is missing
                or empty.
        """
        missing = [field for field in ("app_id", "app_key") if not credentials.get(field)]
        if missing:
            raise CredentialsError(self.SOURCE, missing)

        self._app_id: str = str(credentials["app_id"])
        self._app_key: str = str(credentials["app_key"])
        self._query = query
        self._country = country
        self._location = location
        self._max_pages = max_pages
        self._results_per_page = results_per_page
        self._salary_min = salary_min
        self._distance = distance
        self._max_days_old = max_days_old

    # ------------------------------------------------------------------
    # JobSource interface
    # ------------------------------------------------------------------

    def settings_schema(self) -> dict[str, Any]:
        """Return the credential field definitions for Adzuna.

        Returns:
            Dict with ``app_id`` and ``app_key`` field definitions,
            both marked ``required=True`` and typed as ``"password"``.
        """
        return {
            "app_id": {
                "label": "App ID",
                "type": "password",
                "required": True,
                "help_text": "Found in your Adzuna developer console.",
            },
            "app_key": {
                "label": "App Key",
                "type": "password",
                "required": True,
                "help_text": "Found in your Adzuna developer console.",
            },
        }

    def pages(self) -> Iterator[list[dict[str, Any]]]:
        """Yield raw Adzuna result pages one at a time.

        Fetches pages 1 through ``max_pages`` (inclusive).  Stops early
        if a page returns zero results, which signals that the API has
        no more data for the current query.

        Yields:
            A list of raw Adzuna result dicts for each page.  Each dict
            is passed directly to :meth:`normalise` by the caller.

        Raises:
            ScrapeError: If the HTTP request fails and retries are
                exhausted.
        """
        for page_num in range(1, self._max_pages + 1):
            raw_page = self._fetch_raw_page(page_num)
            if not raw_page:
                logger.info(
                    "Adzuna page %d returned 0 results; stopping early.",
                    page_num,
                )
                return
            yield raw_page

    def normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Map a single Adzuna result dict to the canonical JobRecord shape.

        **Field mapping audit** (spec §9.3):

        Identity fields:
        - ``id``         → ``source_id`` (coerced to str)
        - constant       → ``source`` = ``"adzuna"``
        - constant       → ``description_source`` = ``"snippet"``
          (Adzuna descriptions are truncated — hydrate is required for
          full text)

        Always-present fields:
        - ``title``        → ``title``
        - ``redirect_url`` → ``url``
        - ``created``      → ``posted_at``
        - ``description``  → ``description``

        Optional fields:
        - ``company.display_name`` → ``company``  (None if absent/non-dict)
        - ``location.display_name`` → ``location`` (None if absent/non-dict)
        - ``salary_min``   → ``salary_min``
        - ``salary_max``   → ``salary_max``
        - ``contract_type`` → ``contract_type``
        - ``contract_time`` → ``contract_time``
        - ``salary_currency`` — drop: Adzuna does not expose currency
        - ``salary_period``  — drop: Adzuna does not expose a pay-period
        - ``remote_eligible`` — drop: Adzuna has no remote flag

        Extra blob (Adzuna-specific, marked unstable):
        - ``salary_is_predicted`` → ``extra.salary_is_predicted`` (int)
        - ``category``            → ``extra.category``
        - ``adref``               → ``extra.adref``
        - ``latitude``            → ``extra.latitude``
        - ``longitude``           → ``extra.longitude``

        Args:
            raw: A single entry from the Adzuna ``results`` array.

        Returns:
            A dict conforming to :class:`~job_aggregator.schema.JobRecord`.
        """
        company_obj = raw.get("company")
        location_obj = raw.get("location")

        company: str | None = (
            company_obj.get("display_name") or None if isinstance(company_obj, dict) else None
        )
        location: str | None = (
            location_obj.get("display_name") or None if isinstance(location_obj, dict) else None
        )

        # salary_is_predicted: Adzuna returns "1"/"0" strings or bool/int.
        raw_predicted = raw.get("salary_is_predicted", 0)
        try:
            salary_is_predicted = int(raw_predicted)
        except (TypeError, ValueError):
            salary_is_predicted = 0

        # Build the extra blob for Adzuna-specific fields.
        extra: dict[str, Any] = {"salary_is_predicted": salary_is_predicted}
        for key in ("category", "adref", "latitude", "longitude"):
            value = raw.get(key)
            if value is not None:
                extra[key] = value

        return {
            # Identity
            "source": self.SOURCE,
            "source_id": str(raw.get("id", "")),
            "description_source": "snippet",
            # Always-present
            "title": raw.get("title") or "",
            "url": raw.get("redirect_url") or "",
            "posted_at": raw.get("created") or None,
            "description": raw.get("description") or "",
            # Optional
            "company": company,
            "location": location,
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "salary_currency": None,  # drop: Adzuna does not expose currency
            "salary_period": None,  # drop: Adzuna does not expose pay-period
            "contract_type": raw.get("contract_type") or None,
            "contract_time": raw.get("contract_time") or None,
            "remote_eligible": None,  # drop: Adzuna has no remote flag
            "extra": extra,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_params(self, page: int) -> dict[str, Any]:
        """Build the query-string parameter dict for an API request.

        Args:
            page: 1-based page number.

        Returns:
            Dict of query-string parameters ready to pass to
            :func:`requests.get`.
        """
        params: dict[str, Any] = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "what": self._query,
            "results_per_page": self._results_per_page,
            "content-type": "application/json",
        }
        if self._location:
            params["where"] = self._location
        if self._salary_min:
            params["salary_min"] = self._salary_min
        if self._distance:
            params["distance"] = self._distance
        if self._max_days_old:
            params["max_days_old"] = self._max_days_old
        return params

    def _fetch_raw_page(self, page: int) -> list[dict[str, Any]]:
        """Fetch a single page of raw results from the Adzuna API.

        Retries on HTTP 429 with exponential back-off (2 s, 4 s, 8 s).
        Any other non-200 response is logged and raises
        :exc:`~job_aggregator.errors.ScrapeError`.

        Args:
            page: 1-based page number.

        Returns:
            List of raw result dicts from the ``results`` key, or an
            empty list if the API returned no results.

        Raises:
            ScrapeError: On network failure or persistent rate-limiting.
        """
        url = _ADZUNA_BASE.format(country=self._country, page=page)
        params = self._build_params(page)

        response: requests.Response | None = None

        for attempt, delay in enumerate([0, *_BACKOFF_DELAYS]):
            if delay:
                logger.warning(
                    "Adzuna rate-limited (429); retrying in %d s (attempt %d/%d).",
                    delay,
                    attempt,
                    len(_BACKOFF_DELAYS),
                )
                time.sleep(delay)

            try:
                response = requests.get(url, params=params, timeout=15)
            except requests.RequestException as exc:
                raise ScrapeError(url, str(exc)) from exc

            if response.status_code == 200:
                break
            if response.status_code == 429:
                if attempt < len(_BACKOFF_DELAYS):
                    continue
                raise ScrapeError(
                    url,
                    f"Rate limit not resolved after {len(_BACKOFF_DELAYS)} retries.",
                )
            # Any other non-200 status.
            raise ScrapeError(
                url,
                f"HTTP {response.status_code}",
            )

        if response is None:
            return []

        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:
            raise ScrapeError(url, f"Invalid JSON: {exc}") from exc

        results: list[dict[str, Any]] = data.get("results", [])
        return results
