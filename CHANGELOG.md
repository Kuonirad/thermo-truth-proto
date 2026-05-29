# Changelog

All notable changes to the ThermoTruth Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation
- **Professional README overhaul** - rewritten with accurate badges (PyPI, CI,
  Python, license, code style), a table of contents, a "How It Works" section, a
  reproducible benchmark/results table, and honest project status. Corrected
  stale figures (76 tests, ~2.9k LOC) and broken `thermo-benchmark` flags
  (`--fraction`, throughput's `--duration`), fixed the X.com link, and added
  Contributing / Security / Citation sections.

### Fixed
- **Adaptive difficulty Byzantine term was dead code** - `_estimate_byzantine_fraction`
  compared raw Shannon entropy against `log2(n)`, but entropy is bounded above by
  `log2(n)`, so the estimate was always `0.0` and the Byzantine multiplier never
  engaged. Now derived from *normalized* ensemble disorder (`H / log2(n)`).
- **Energy-cost estimate diverged from real PoW** - `estimate_energy_cost` used
  `16 ** difficulty` while mining/verification use `int(difficulty)` leading hex
  zeros, so the energy-budget check overestimated cost for fractional difficulties.
  It now uses `16 ** int(difficulty)`.
- **Annealing crashed on zero steps** - `converge` and `converge_with_tempering`
  raised `UnboundLocalError` when `max_steps <= 0`; metrics are now seeded from the
  initial ensemble.
- **Genesis state broke gRPC serialization** - non-string metadata values
  (e.g. `{"genesis": True}`) could not be packed into the protobuf
  `map<string, string>` field, silently emptying `RequestStates`/`SyncState`
  responses. Added `network.utils.stringify_metadata` and applied it at all
  serialization sites.
- **Local `pytest` always failed on coverage** - `pytest.ini` pinned
  `--cov-fail-under=80` while real coverage was ~32% (CI masked it with `=0`).
  Now an enforced, realistic floor (raised to 50 as the suite grew).
- **Node excluded its own proposal from consensus** - the `cli.node` consensus
  loop broadcast each proposal to peers but never recorded it locally, so a node
  ran consensus purely on peer states. Added `ThermoTruthNode.propose_and_record`,
  which mines and records the node's own state.
- **Misleading `°C` temperature unit** - consensus "temperature" is a
  variance-based thermodynamic analog, not degrees Celsius. Removed the `°C`
  suffix from CLI/server output.

### Added
- `tests/test_audit_regressions.py` - regression coverage for the core bugs
- `tests/test_cli_benchmark.py` and `tests/test_network_server.py` - coverage for
  the CLI/benchmark helpers and the gRPC servicer (raised total coverage ~32% -> ~56%)
- `ThermoTruthNode.propose_and_record` helper
- Production-grade publishing pipeline with PyPI trusted publishing
- GitHub Packages mirror for enterprise users
- Sigstore keyless signing for all releases
- SLSA Level 3 provenance attestation
- CycloneDX SBOM generation
- Comprehensive RELEASING.md documentation

## [1.1.0] - 2025-12-03

### Fixed
- **Byzantine filtering threshold** - Replaced mean/std with Median Absolute Deviation (MAD) for robust outlier detection
  - Improved Byzantine tolerance from <30% to **40%** (exceeds standard BFT 33% limit)
  - Error reduction: 98-99% at 30-40% Byzantine nodes
  - Validated with real protocol execution (not simulation)
  - See `validation/BYZANTINE_FIX_REPORT.md` for full analysis

### Changed
- `ThermodynamicEnsemble.filter_byzantine_states()` now uses MAD-based modified Z-scores
- Default filtering threshold changed from 3.0 to 2.5 (more aggressive filtering)

### Added
- `validation/byzantine_threshold_test.py` - Real Byzantine resilience testing
- `validation/BYZANTINE_FIX_REPORT.md` - Comprehensive fix documentation

## [1.0.1] - 2025-12-01

### Fixed
- Updated copyright notice in README to "Kevin KULL"
- Corrected author attribution throughout documentation

## [1.0.0] - 2025-12-01

### Added
- Complete thermodynamic consensus protocol implementation
- Core modules:
  - `state.py`: Consensus state and thermodynamic ensemble (313 lines)
  - `pow.py`: Proof-of-Work with adaptive difficulty (293 lines)
  - `annealing.py`: Simulated annealing and parallel tempering (416 lines)
  - `protocol.py`: Main protocol integration (331 lines)
- Network layer with gRPC and Protocol Buffers (1,048 lines)
- CLI tools: node runtime, client, and benchmarking suite (704 lines)
- Real benchmarks with measured performance data
- 41 unit tests with 90%+ core coverage
- CI/CD pipeline with GitHub Actions
- Docker environment for multi-node deployment
- Pre-commit hooks and code formatting (Black)
- Comprehensive documentation

### Fixed
- **Critical**: PoW timestamp validation bug
  - `mine()` now returns timestamp used for hashing
  - `create_pow_state()` uses same timestamp to prevent validation failures
- Module import configuration in `setup.py`
- CI package installation workflow

### Security
- All tests passing (41/41)
- Code Resurrection Protocol (CRP) compliant
- Production-ready codebase

### Documentation
- Complete whitepaper
- Implementation summary
- CRP compliance report
- API documentation
- Usage examples

## [0.1.0] - 2025-11-30 (Pre-release)

### Added
- Initial project structure
- Theoretical whitepaper
- Mock benchmarks (replaced in v1.0.0)

---

## Release Notes Format

### Added
New features and capabilities.

### Changed
Changes to existing functionality.

### Deprecated
Features that will be removed in future versions.

### Removed
Features that have been removed.

### Fixed
Bug fixes.

### Security
Security-related changes and fixes.

---

[Unreleased]: https://github.com/Kuonirad/thermo-truth-proto/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Kuonirad/thermo-truth-proto/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/Kuonirad/thermo-truth-proto/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Kuonirad/thermo-truth-proto/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/Kuonirad/thermo-truth-proto/releases/tag/v0.1.0
