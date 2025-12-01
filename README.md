# ThermoTruth Protocol: Thermodynamic Consensus for Sybil-Resistant Networks

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)

**Thermodynamic Truth** is a novel consensus protocol that leverages physical laws—specifically energy conservation and entropy minimization—to achieve Byzantine Fault Tolerance (BFT) in open, permissionless networks.

Unlike traditional BFT protocols that rely on voting (communication-heavy) or Proof-of-Work that relies on lottery (energy-wasteful), ThermoTruth uses **Proof-of-Work as a thermodynamic cost function** to secure the network against Sybil attacks while maintaining **$O(n)$ scalability**.

![Dashboard](docs/dashboard_annotated.png)

## 🚀 Key Claims

Based on experimental results (see `docs/results_section.pdf`):

1.  **Linear Scalability**: Achieves **$O(n)$ latency scaling**, maintaining sub-second finality (500ms) at 100 nodes.
2.  **Throughput Saturation**: Sustains **200 TPS** regardless of cluster size, outperforming HoneyBadger BFT by **50x**.
3.  **Byzantine Resilience**: Self-heals under 33% Byzantine attacks with consensus error staying below **0.05°C**.
4.  **Bandwidth Efficiency**: Reduces network bandwidth by **90%** compared to asynchronous BFT alternatives.
5.  **Thermodynamic Necessity**: Removing PoW results in a **6000% increase** in consensus error, validating the physics-based security model.

## 📦 Installation

```bash
pip install thermodynamic-truth
```

## ⚡ Quick Start

Start a local 4-node cluster:

```bash
# Terminal 1: Start the bootstrap node
python -m thermodynamic_truth.node --id 0 --port 50051

# Terminal 2: Start a peer
python -m thermodynamic_truth.node --id 1 --port 50052 --peer localhost:50051
```

See [Quick Start Guide](docs/QUICK_START_GUIDE.pdf) for detailed operator instructions.

## 📂 Repository Structure

*   `src/`: Core protocol implementation (Python).
*   `benchmarks/`: Scripts for reproducing the experimental results (PBFT/HBBFT comparison).
*   `docs/`: Research papers, test plans, and guides.
*   `examples/`: Sample applications and deployment configurations.

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 ThermoTruth Initiative.
