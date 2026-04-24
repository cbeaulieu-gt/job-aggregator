"""Tests for scripts/preflight_smoke.py.

Covers:
- Source registry (all 10 expected sources present)
- Argument parsing (--dry-run default, --live, --only, --skip)
- Credential resolution (present / missing / partial)
- Source filtering (--only, --skip, combined)
- Call-cap assertion (total_calls <= 10)
- ProbeResult classification logic (green / needs-fixing / broken)
- Dry-run output does not make HTTP requests
- Markdown report generation
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: ensure scripts/ is importable as a plain module.
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import preflight_smoke as ps  # noqa: E402  (import after path surgery)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_SOURCES = [
    "adzuna",
    "arbeitnow",
    "himalayas",
    "jobicy",
    "jooble",
    "jsearch",
    "remoteok",
    "remotive",
    "the_muse",
    "usajobs",
]


# ---------------------------------------------------------------------------
# Source registry tests
# ---------------------------------------------------------------------------


class TestSourceRegistry:
    """Verify the SOURCE_CONFIGS registry is complete and well-formed."""

    def test_all_ten_sources_registered(self) -> None:
        """SOURCE_CONFIGS must contain exactly the 10 expected source keys."""
        registered = set(ps.SOURCE_CONFIGS.keys())
        assert registered == set(ALL_SOURCES)

    def test_each_source_has_required_keys(self) -> None:
        """Every source config must have url, params, and cred_keys entries."""
        required_keys = {"url", "params", "cred_keys"}
        for name, cfg in ps.SOURCE_CONFIGS.items():
            missing = required_keys - set(cfg.keys())
            assert not missing, f"Source {name!r} config missing keys: {missing}"

    def test_cred_sources_list_required_env_vars(self) -> None:
        """Sources requiring credentials must declare non-empty cred_keys."""
        cred_sources = {"adzuna", "jooble", "jsearch", "usajobs"}
        for name in cred_sources:
            assert ps.SOURCE_CONFIGS[name]["cred_keys"], (
                f"Source {name!r} should list credential env-var names"
            )

    def test_no_cred_sources_have_empty_cred_keys(self) -> None:
        """Sources that need no credentials must have empty cred_keys."""
        no_cred_sources = {
            "arbeitnow",
            "himalayas",
            "jobicy",
            "remoteok",
            "remotive",
            "the_muse",
        }
        for name in no_cred_sources:
            assert ps.SOURCE_CONFIGS[name]["cred_keys"] == [], (
                f"Source {name!r} should have empty cred_keys"
            )


# ---------------------------------------------------------------------------
# Argument parsing tests
# ---------------------------------------------------------------------------


class TestArgumentParsing:
    """Verify CLI argument parsing behaviour."""

    def _parse(self, argv: list[str]) -> argparse.Namespace:
        """Parse argv without sys.argv side-effects."""
        return cast(argparse.Namespace, ps.build_arg_parser().parse_args(argv))

    def test_default_mode_is_dry_run(self) -> None:
        """Running with no flags must default to dry-run mode."""
        args = self._parse([])
        assert args.dry_run is True
        assert args.live is False

    def test_live_flag_disables_dry_run(self) -> None:
        """Passing --live must set live=True and dry_run=False."""
        args = self._parse(["--live"])
        assert args.live is True
        assert args.dry_run is False

    def test_only_parses_comma_separated_sources(self) -> None:
        """--only adzuna,jooble must produce a list of two source names."""
        args = self._parse(["--only", "adzuna,jooble"])
        assert args.only == ["adzuna", "jooble"]

    def test_skip_parses_comma_separated_sources(self) -> None:
        """--skip jsearch,usajobs must produce a list of two source names."""
        args = self._parse(["--skip", "jsearch,usajobs"])
        assert args.skip == ["jsearch", "usajobs"]

    def test_only_default_is_none(self) -> None:
        """--only omitted must give None (meaning: run all sources)."""
        args = self._parse([])
        assert args.only is None

    def test_skip_default_is_empty_list(self) -> None:
        """--skip omitted must give an empty list."""
        args = self._parse([])
        assert args.skip == []


# ---------------------------------------------------------------------------
# Source-selection (filtering) tests
# ---------------------------------------------------------------------------


class TestSourceSelection:
    """Verify resolve_sources applies --only and --skip correctly."""

    def test_no_filters_returns_all_ten(self) -> None:
        """With no filters, all 10 sources should be selected."""
        sources = ps.resolve_sources(only=None, skip=[])
        assert set(sources) == set(ALL_SOURCES)
        assert len(sources) == 10

    def test_only_filter_limits_to_named_sources(self) -> None:
        """--only adzuna,jooble must return exactly those two sources."""
        sources = ps.resolve_sources(only=["adzuna", "jooble"], skip=[])
        assert sources == ["adzuna", "jooble"]

    def test_skip_filter_excludes_named_source(self) -> None:
        """--skip jsearch must exclude jsearch from the result."""
        sources = ps.resolve_sources(only=None, skip=["jsearch"])
        assert "jsearch" not in sources
        assert len(sources) == 9

    def test_only_and_skip_combined(self) -> None:
        """--only a,b,c --skip b must return [a, c]."""
        sources = ps.resolve_sources(
            only=["adzuna", "jooble", "jsearch"],
            skip=["jooble"],
        )
        assert sources == ["adzuna", "jsearch"]

    def test_unknown_only_source_raises(self) -> None:
        """--only with an unknown source name must raise ValueError."""
        with pytest.raises(ValueError, match="unknown source"):
            ps.resolve_sources(only=["nonexistent_source"], skip=[])

    def test_unknown_skip_source_raises(self) -> None:
        """--skip with an unknown source name must raise ValueError."""
        with pytest.raises(ValueError, match="unknown source"):
            ps.resolve_sources(only=None, skip=["nonexistent_source"])


# ---------------------------------------------------------------------------
# Call-cap assertion test
# ---------------------------------------------------------------------------


class TestCallCap:
    """The hard cap of 10 total calls must be enforced."""

    def test_call_cap_assertion_passes_for_ten(self) -> None:
        """assert_call_cap must not raise when total_calls <= 10."""
        ps.assert_call_cap(10)  # should not raise

    def test_call_cap_assertion_passes_for_fewer(self) -> None:
        """assert_call_cap must not raise when total_calls < 10."""
        ps.assert_call_cap(3)

    def test_call_cap_assertion_raises_for_eleven(self) -> None:
        """assert_call_cap must raise AssertionError when total > 10."""
        with pytest.raises(AssertionError):
            ps.assert_call_cap(11)


# ---------------------------------------------------------------------------
# Credential resolution tests
# ---------------------------------------------------------------------------


class TestCredentialResolution:
    """Verify load_creds reads env vars and reports missing ones."""

    def test_returns_present_creds(self) -> None:
        """load_creds returns values for env vars that are set."""
        env = {"ADZUNA_APP_ID": "myid", "ADZUNA_APP_KEY": "mykey"}
        with patch.dict("os.environ", env, clear=True):
            creds, missing = ps.load_creds(["ADZUNA_APP_ID", "ADZUNA_APP_KEY"])
        assert creds == {"ADZUNA_APP_ID": "myid", "ADZUNA_APP_KEY": "mykey"}
        assert missing == []

    def test_reports_missing_creds(self) -> None:
        """load_creds reports names of env vars that are absent."""
        with patch.dict("os.environ", {}, clear=True):
            creds, missing = ps.load_creds(["ADZUNA_APP_ID", "ADZUNA_APP_KEY"])
        assert creds == {}
        assert set(missing) == {"ADZUNA_APP_ID", "ADZUNA_APP_KEY"}

    def test_partial_creds_reported_correctly(self) -> None:
        """load_creds handles the case where only some vars are set."""
        env = {"ADZUNA_APP_ID": "myid"}
        with patch.dict("os.environ", env, clear=True):
            creds, missing = ps.load_creds(["ADZUNA_APP_ID", "ADZUNA_APP_KEY"])
        assert creds == {"ADZUNA_APP_ID": "myid"}
        assert missing == ["ADZUNA_APP_KEY"]

    def test_empty_cred_keys_returns_empty_dicts(self) -> None:
        """load_creds with no required keys returns empty creds and missing."""
        creds, missing = ps.load_creds([])
        assert creds == {}
        assert missing == []


# ---------------------------------------------------------------------------
# ProbeResult classification tests
# ---------------------------------------------------------------------------


class TestProbeResultClassification:
    """Verify classify_response maps HTTP + shape outcomes to status strings."""

    def _mock_response(
        self,
        status_code: int,
        json_data: Any,
    ) -> MagicMock:
        """Build a minimal mock resembling a requests.Response."""
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        return resp

    def test_http_200_with_listings_is_green(self) -> None:
        """HTTP 200 with at least one listing classifies as green."""
        resp = self._mock_response(200, {"results": [{"title": "Dev"}]})
        result = ps.classify_response("adzuna", resp, listing_key="results")
        assert result.status == "green"

    def test_http_200_with_empty_listings_is_needs_fixing(self) -> None:
        """HTTP 200 but zero listings classifies as needs-fixing."""
        resp = self._mock_response(200, {"results": []})
        result = ps.classify_response("adzuna", resp, listing_key="results")
        assert result.status == "needs-fixing"

    def test_http_200_missing_listing_key_is_needs_fixing(self) -> None:
        """HTTP 200 but expected key absent classifies as needs-fixing."""
        resp = self._mock_response(200, {"unexpected_key": []})
        result = ps.classify_response("adzuna", resp, listing_key="results")
        assert result.status == "needs-fixing"

    def test_http_401_is_broken(self) -> None:
        """HTTP 401 (auth failure) classifies as broken-defer-to-v1.1."""
        resp = self._mock_response(401, {})
        result = ps.classify_response("adzuna", resp, listing_key="results")
        assert result.status == "broken-defer-to-v1.1"

    def test_http_404_is_broken(self) -> None:
        """HTTP 404 (endpoint dead) classifies as broken-defer-to-v1.1."""
        resp = self._mock_response(404, {})
        result = ps.classify_response("adzuna", resp, listing_key="results")
        assert result.status == "broken-defer-to-v1.1"

    def test_http_429_is_broken(self) -> None:
        """HTTP 429 (rate-limited) classifies as broken-defer-to-v1.1."""
        resp = self._mock_response(429, {})
        result = ps.classify_response("adzuna", resp, listing_key="results")
        assert result.status == "broken-defer-to-v1.1"

    def test_result_carries_source_name(self) -> None:
        """ProbeResult.source must match the source name passed in."""
        resp = self._mock_response(200, {"results": [{"title": "x"}]})
        result = ps.classify_response("jooble", resp, listing_key="results")
        assert result.source == "jooble"


# ---------------------------------------------------------------------------
# Dry-run tests (no HTTP calls made)
# ---------------------------------------------------------------------------


class TestDryRun:
    """Dry-run mode must never make network requests."""

    def test_dry_run_returns_results_without_http(self) -> None:
        """probe_source in dry-run mode must not call requests.get."""
        with patch("preflight_smoke.requests") as mock_requests:
            result = ps.probe_source("adzuna", dry_run=True, creds={})
        mock_requests.get.assert_not_called()
        assert result.status == "dry-run"

    def test_dry_run_result_source_matches(self) -> None:
        """Dry-run ProbeResult.source must match the source argument."""
        result = ps.probe_source("himalayas", dry_run=True, creds={})
        assert result.source == "himalayas"


# ---------------------------------------------------------------------------
# Markdown report generation tests
# ---------------------------------------------------------------------------


class TestMarkdownReport:
    """Verify render_markdown_report produces valid markdown output."""

    def _make_result(self, source: str, status: str, note: str = "") -> ps.ProbeResult:
        """Construct a ProbeResult for testing."""
        return ps.ProbeResult(source=source, status=status, note=note)

    def test_dry_run_report_contains_banner(self) -> None:
        """Dry-run report must start with the DRY RUN banner."""
        results = [self._make_result("adzuna", "dry-run")]
        md = ps.render_markdown_report(results, dry_run=True)
        assert "DRY RUN" in md

    def test_live_report_does_not_contain_dry_run_banner(self) -> None:
        """Live report must not contain the DRY RUN marker."""
        results = [self._make_result("adzuna", "green")]
        md = ps.render_markdown_report(results, dry_run=False)
        assert "DRY RUN" not in md

    def test_report_contains_all_source_names(self) -> None:
        """Report table must include a row for every source in results."""
        results = [self._make_result(s, "green") for s in ALL_SOURCES]
        md = ps.render_markdown_report(results, dry_run=False)
        for source in ALL_SOURCES:
            assert source in md

    def test_report_contains_status_values(self) -> None:
        """Status values must appear in the report table."""
        results = [
            self._make_result("adzuna", "green"),
            self._make_result("jooble", "needs-fixing", "shape drift"),
            self._make_result("jsearch", "broken-defer-to-v1.1", "403"),
        ]
        md = ps.render_markdown_report(results, dry_run=False)
        assert "green" in md
        assert "needs-fixing" in md
        assert "broken-defer-to-v1.1" in md

    def test_report_is_markdown_table(self) -> None:
        """Report must contain markdown table delimiters."""
        results = [self._make_result("adzuna", "green")]
        md = ps.render_markdown_report(results, dry_run=False)
        assert "|" in md
        assert "---" in md
