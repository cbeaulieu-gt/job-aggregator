# job-aggregator

Reusable job aggregation library: pluggable source plugins, normalized output, no scoring or DB dependencies.

[![PyPI version](https://img.shields.io/pypi/v/job-aggregator)](https://pypi.org/project/job-aggregator/)
[![CI](https://github.com/cbeaulieu-gt/job-aggregator/actions/workflows/ci.yml/badge.svg)](https://github.com/cbeaulieu-gt/job-aggregator/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/job-aggregator)](https://pypi.org/project/job-aggregator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install job-aggregator
```

## Quickstart

```bash
# List available plugins and whether credentials are configured
job-aggregator sources

# Fetch listings and enrich with full descriptions in a pipeline
job-aggregator jobs --query "python developer" --hours 24 \
  | job-aggregator hydrate > full.jsonl
```

Each line of `full.jsonl` after the first is a normalized job record. The
first line is the output envelope (see [docs/output_schema.md](docs/output_schema.md)
for the full field reference).

To use sources that require API credentials, pass a credentials file:

```bash
job-aggregator jobs --query "python developer" \
  --credentials ~/.job-aggregator/creds.json \
  | job-aggregator hydrate > full.jsonl
```

See [docs/credentials_format.md](docs/credentials_format.md) for the
credentials file format and per-plugin field requirements.

## Documentation

- [Output Schema](docs/output_schema.md) — envelope structure, record fields,
  `description_source` truth table, versioning policy, and supported sources.
- [Plugin Authoring Guide](docs/plugin_authoring.md) — how to write and
  register a new source plugin.
- [Credentials Format](docs/credentials_format.md) — credentials file format
  and per-plugin field requirements.

## Status

**Pre-1.0 / Alpha.** The public API, output schema, and credentials format
are under active development and may change between releases until `v1.0.0`
is tagged.
