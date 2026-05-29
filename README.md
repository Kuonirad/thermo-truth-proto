# ThermoTruth Protocol

### Thermodynamic Consensus for Sybil-Resistant Networks

[![PyPI version](https://img.shields.io/pypi/v/thermodynamic-truth.svg)](https://pypi.org/project/thermodynamic-truth/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/Kuonirad/thermo-truth-proto/actions/workflows/ci.yml/badge.svg)](https://github.com/Kuonirad/thermo-truth-proto/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://pypi.org/project/thermodynamic-truth/)

**ThermoTruth** is a consensus protocol that treats agreement as a *physical*
process. Node proposals form a statistical ensemble whose **temperature**
(disagreement), **entropy** (disorder), and **free energy** are measured
directly; simulated annealing then drives that ensemble toward a low-energy,
high-coherence consensus state. Proof-of-Work is repurposed not as a lottery but
as a **thermodynamic cost function** that makes Sybil identities expensive while
preserving **O(n)** scalability.

> **Author:** Kevin KULL · **X:** [@KULLAILABS](https://x.com/KULLAILABS)

![ThermoTruth consensus dashboard](docs/dashboard_annotated.png)

---

## Table of Contents

- [Why ThermoTruth](#why-thermotruth)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Benchmarks & Results](#benchmarks--results)
- [Project Status](#project-status)
- [Repository Layout](#repository-layout)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Security](#security)
- [Citation](#citation)
- [License](#license)

---

## Why ThermoTruth

Classical Byzantine-fault-tolerant (BFT) protocols trade off along two axes:

| Approach | Mechanism | Cost |
| --- | --- | --- |
| Voting BFT (PBFT, HotStuff) | All-to-all messaging | O(n²) communication |
| Nakamoto PoW | Hash lottery | High energy, probabilistic finality |
| **ThermoTruth** | **Energy-weighted thermodynamic ensemble** | **O(n) latency, deterministic free-energy minimization** |

By modeling consensus as free-energy minimization, ThermoTruth gets robust
outlier rejection and Sybil resistance from the same physical framework instead
of bolting them on separately.

## How It Works

1. **Proposal.** Each node proposes a `ConsensusState` — a state vector plus a
   Proof-of-Work whose difficulty adapts to network entropy and estimated
   Byzantine activity.
2. **Ensemble metrics.** Proposals are collected into a `ThermodynamicEnsemble`
   that computes its temperature (∝ proposal variance), Shannon entropy, and
   Helmholtz free energy `F = U − T·S`.
3. **Byzantine filtering.** Outliers are removed with a **Median Absolute
   Deviation (MAD)** modified z-score — robust to contamination that would
   inflate a naïve mean/standard-deviation filter.
4. **Annealing.** Simulated annealing with parallel tempering (replica exchange)
   drives the ensemble toward minimal free energy and sub-threshold variance.
5. **Extraction.** The agreed value is the **Boltzmann (energy-weighted) mean**
   of the surviving states — proposals backed by more work weigh more.

The full engine lives in [`src/thermodynamic_truth/core/`](src/thermodynamic_truth/core/)
(`state.py`, `pow.py`, `annealing.py`, `protocol.py`), with a gRPC transport in
[`network/`](src/thermodynamic_truth/network/) and CLIs in
[`cli/`](src/thermodynamic_truth/cli/).

## Installation

### From PyPI

```bash
pip install thermodynamic-truth
```

### From source (development)

```bash
git clone https://github.com/Kuonirad/thermo-truth-proto.git
cd thermo-truth-proto

# Editable install with dev extras (pytest, black, flake8, mypy)
pip install -e ".[dev]"

# Run the test suite
pytest
```

**Requirements:** Python 3.9+ · NumPy · gRPC (`grpcio`, `protobuf`).

## Quick Start

### Run a local cluster

```bash
# Terminal 1 — genesis node
thermo-node --id node0 --port 50051 --genesis

# Terminal 2 — peer node
thermo-node --id node1 --port 50052 --peer localhost:50051
```

### Inspect a running node

```bash
thermo-client ping localhost:50051
thermo-client status localhost:50051
```

### Run benchmarks

```bash
# Consensus latency
thermo-benchmark latency --nodes 10 --rounds 10

# Byzantine resilience (fraction of malicious nodes)
thermo-benchmark byzantine --nodes 15 --fraction 0.40 --rounds 5

# Sustained throughput (runs for the given duration, in seconds)
thermo-benchmark throughput --duration 60
```

### Docker cluster

```bash
docker-compose up        # start a multi-node cluster
docker-compose logs -f   # follow logs
```

See the [Quick Start Guide](docs/QUICK_START_GUIDE.pdf) for a detailed walkthrough.

## Benchmarks & Results

All figures are produced by the executable suite in
[`benchmarks/`](benchmarks/) and the `thermo-benchmark` CLI — reproduce them
locally with the commands above. Detailed methodology is in
[`docs/results_section.pdf`](docs/results_section.pdf).

| Property | Result | Notes |
| --- | --- | --- |
| **Scalability** | ~O(n) latency, sub-second finality at 100 nodes | `thermo-benchmark scaling` |
| **Throughput** | Saturates at ~200 TPS independent of cluster size | `thermo-benchmark throughput` |
| **Byzantine tolerance** | **Self-heals at 40% malicious nodes** (> classical 33% BFT bound) | MAD filter, v1.1.0 |
| **Bandwidth** | ~90% lower than asynchronous BFT baselines | see results report |
| **Thermodynamic necessity** | Removing PoW sharply increases consensus error | `ablation_study_real.py` |

**Reproduced Byzantine run** (15 nodes, 40% malicious, 5 rounds): the MAD filter
removed all 6 malicious proposals every round and post-filter variance held at
~0.006 — well below the 0.05 consensus threshold.

> Performance numbers depend on hardware and configuration; treat the table as
> indicative of the included benchmarks rather than a service-level guarantee.

## Project Status

ThermoTruth is published on PyPI and exercised by CI across Python 3.9–3.11, but
it remains a **research-stage (alpha)** protocol — see the `Development Status ::
3 - Alpha` classifier. It is intended for experimentation and study, not yet for
securing production value.

- ✅ Core protocol, gRPC networking, and CLIs implemented
- ✅ Continuous integration: tests, formatting, linting, build, and Docker
- ✅ Distributed via PyPI trusted publishing (OIDC) with Sigstore signing
- ✅ 76 automated tests
- ⚠️ Alpha API — interfaces may change between minor versions

## Repository Layout

```
thermo-truth-proto/
├── src/thermodynamic_truth/   # Library (~2.9k LOC of hand-written Python)
│   ├── core/                  # Protocol engine: state, PoW, annealing, protocol
│   ├── network/               # gRPC server, client, and (de)serialization
│   └── cli/                   # thermo-node, thermo-client, thermo-benchmark
├── tests/                     # Test suite (76 tests)
├── benchmarks/                # Executable benchmark suite
├── validation/                # Byzantine-resilience validation
├── docs/                      # Documentation (start at docs/INDEX.md)
├── CHANGELOG.md               # Version history (Keep a Changelog)
├── RELEASING.md               # Release process
├── SECURITY.md                # Security policy
└── docker-compose.yml         # Multi-node deployment
```

## Documentation

- **[docs/INDEX.md](docs/INDEX.md)** — full documentation index (start here)
- [Whitepaper](docs/whitepaper.md) — protocol design and theory
- [Results section](docs/results_section.pdf) — benchmark methodology & data
- [Quick Start Guide](docs/QUICK_START_GUIDE.pdf)
- [CHANGELOG](CHANGELOG.md)

## Contributing

Contributions are welcome. Please:

1. Open an issue describing the change before large PRs.
2. Keep the suite green: `pytest`, `black src/ tests/`, and
   `flake8 src/ tests/`.
3. Add tests for new behavior and update `CHANGELOG.md` under `[Unreleased]`.

The repository ships a [pre-commit](.pre-commit-config.yaml) configuration —
install it with `pre-commit install`.

## Security

Please report vulnerabilities responsibly as described in
[SECURITY.md](SECURITY.md). Do not open public issues for security-sensitive
reports.

## Citation

If you use ThermoTruth in academic work, please cite it:

```bibtex
@software{kull_thermotruth,
  author  = {Kull, Kevin},
  title   = {ThermoTruth Protocol: Thermodynamic Consensus for Sybil-Resistant Networks},
  url      = {https://github.com/Kuonirad/thermo-truth-proto},
  version = {1.1.0},
  year    = {2025}
}
```

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE).

Copyright © 2025–2026 Kevin KULL.
