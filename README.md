# job-aggregator

Reusable job aggregation library: pluggable source plugins, normalized output, no scoring or DB dependencies.

[![PyPI version](https://img.shields.io/pypi/v/job-aggregator)](https://pypi.org/project/job-aggregator/)
[![CI](https://github.com/cbeaulieu-gt/job-aggregator/actions/workflows/ci.yml/badge.svg)](https://github.com/cbeaulieu-gt/job-aggregator/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/job-aggregator)](https://pypi.org/project/job-aggregator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Status

**Pre-1.0 / Alpha.** The public API, output schema, and credentials format
are under active development and may change between releases until `v1.0.0`
is tagged. See the [design spec](docs/superpowers/specs/2026-04-23-job-aggregator-design.md)
for the full architecture and the execution plan for the delivery roadmap.

## Installation

```bash
pip install job-aggregator
```

> **Note:** This requires v1.0.0 to be published to PyPI. Pre-release
> versions (`v1.0.0-rc*`) are available on
> [TestPyPI](https://test.pypi.org/project/job-aggregator/) once the
> Code-complete gate is reached.

## Quickstart

```python
# Coming soon — see issues #16, #17, #18
```

## Design documentation

See [`docs/superpowers/specs/2026-04-23-job-aggregator-design.md`](docs/superpowers/specs/2026-04-23-job-aggregator-design.md)
for the full design specification, including the output schema, plugin
contract, credentials format, and CLI surface.
