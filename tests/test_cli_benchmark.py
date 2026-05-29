"""
Tests for the CLI / benchmark layer.

Covers the previously-untested ``cli.benchmark`` pure functions and the
``cli.node`` proposal-recording fix:

- ``ThermoTruthNode.propose_and_record`` must add the node's own proposal to its
  ensemble (regression: the consensus loop used to broadcast its proposal to
  peers but never record it locally, so the node excluded its own opinion).
- The benchmark helpers must return well-formed result dicts and actually
  filter Byzantine outliers.
"""

import numpy as np

from thermodynamic_truth.cli import benchmark as bench
from thermodynamic_truth.cli.node import ThermoTruthNode


class TestNodeProposeAndRecord:
    """Regression: a node must include its own proposal in its ensemble."""

    def _node(self):
        # No peers and we never call start(), so no socket is bound.
        return ThermoTruthNode(node_id="solo", port=0, peers=[], pow_difficulty=1.0)

    def test_proposal_is_recorded_locally(self):
        node = self._node()
        assert len(node.protocol.current_ensemble.states) == 0
        state = node.propose_and_record(np.array([0.1, 0.2, 0.3]))
        assert state is not None
        # The node's own state must now be in its ensemble.
        assert len(node.protocol.current_ensemble.states) == 1
        assert node.protocol.current_ensemble.states[0].proposer_id == "solo"

    def test_failed_proposal_records_nothing(self, monkeypatch):
        node = self._node()
        monkeypatch.setattr(node.protocol, "propose_state", lambda *a, **k: None)
        assert node.propose_and_record(np.zeros(3)) is None
        assert len(node.protocol.current_ensemble.states) == 0


class TestBenchmarkLatency:
    def test_returns_expected_shape(self):
        result = bench.benchmark_latency(n_nodes=4, n_rounds=3)
        assert result["n_nodes"] == 4
        assert result["n_rounds"] == 3
        assert len(result["latencies"]) == 3
        assert len(result["variances"]) == 3
        assert result["avg_latency"] >= 0.0
        assert result["max_latency"] >= result["min_latency"]


class TestBenchmarkByzantine:
    def test_filters_outliers(self):
        result = bench.benchmark_byzantine_resilience(
            n_nodes=12, byzantine_fraction=0.25, n_rounds=3
        )
        assert result["n_byzantine"] == 3
        assert result["n_nodes"] == 12
        # With clear honest/Byzantine separation the filter should remove states
        # on average across rounds.
        assert result["avg_filtered"] > 0.0


class TestBenchmarkThroughput:
    def test_runs_for_short_duration(self):
        # Duration 0 means the while-loop condition is immediately false, but the
        # function must still return a well-formed dict without dividing by zero
        # on a positive elapsed time.
        result = bench.benchmark_throughput(duration=0)
        assert set(result) == {"duration", "transactions", "rounds", "tps"}
        assert result["tps"] >= 0.0


def test_no_celsius_unit_leaks_in_cli():
    """The misleading '°C' label must not reappear in shipped CLI/server code."""
    import pathlib

    src = pathlib.Path(bench.__file__).resolve().parents[1]
    offenders = [p for p in src.rglob("*.py") if "°C" in p.read_text(encoding="utf-8")]
    assert offenders == [], f"Found '°C' in: {offenders}"
