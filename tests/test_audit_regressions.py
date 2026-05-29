"""
Regression tests for bugs found during the full-codebase audit.

Each test pins a specific defect so it cannot silently return:

- Bug A: ``_estimate_byzantine_fraction`` was dead code (entropy can never
  exceed log2(n)), so the Byzantine term of adaptive difficulty never engaged.
- Bug B: ``estimate_energy_cost`` used ``16 ** difficulty`` while mining uses
  ``int(difficulty)`` leading zeros, wildly overestimating cost.
- Bug C: ``converge``/``converge_with_tempering`` raised ``UnboundLocalError``
  when ``max_steps <= 0``.
- Bug D: genesis metadata ``{"genesis": True}`` could not be serialized into the
  protobuf ``map<string, string>`` metadata field.
"""

import numpy as np
import pytest

from thermodynamic_truth.core.protocol import ThermodynamicTruth
from thermodynamic_truth.core.pow import ProofOfWork
from thermodynamic_truth.core.state import (
    ConsensusState,
    ThermodynamicEnsemble,
    create_genesis_state,
)
from thermodynamic_truth.core.annealing import ThermodynamicAnnealer


def _state(vec, proposer):
    return ConsensusState(
        state_vector=np.array(vec, dtype=np.float64),
        energy=1e-6,
        timestamp=0.0,
        proposer_id=proposer,
        nonce=0,
        difficulty=0.0,
    )


class TestByzantineFractionEstimate:
    """Bug A: the heuristic must actually react to disorder."""

    def test_full_agreement_is_zero(self):
        proto = ThermodynamicTruth(node_id="n", use_parallel_tempering=False)
        for i in range(8):
            proto.current_ensemble.add_state(_state([1.0], f"n{i}"))
        assert proto._estimate_byzantine_fraction() == 0.0

    def test_full_disagreement_is_positive_and_capped(self):
        proto = ThermodynamicTruth(node_id="n", use_parallel_tempering=False)
        # Every node proposes a distinct vector -> maximum disorder.
        for i in range(8):
            proto.current_ensemble.add_state(_state([float(i)], f"n{i}"))
        frac = proto._estimate_byzantine_fraction()
        assert frac == pytest.approx(0.5)
        assert 0.0 <= frac <= 0.5

    def test_monotonic_in_disorder(self):
        """More distinct minority vectors -> not-smaller Byzantine estimate."""
        low = ThermodynamicTruth(node_id="lo", use_parallel_tempering=False)
        for i in range(8):
            low.current_ensemble.add_state(_state([1.0], f"a{i}"))  # all agree
        high = ThermodynamicTruth(node_id="hi", use_parallel_tempering=False)
        for i in range(8):
            high.current_ensemble.add_state(_state([float(i)], f"b{i}"))  # all disagree
        assert high._estimate_byzantine_fraction() >= low._estimate_byzantine_fraction()


class TestEnergyEstimateMatchesMining:
    """Bug B: energy estimate must track the integer leading-zero target."""

    def test_fractional_difficulty_uses_integer_zeros(self):
        pow_engine = ProofOfWork(base_difficulty=2.0, energy_per_hash=1e-9)
        # 2.0, 2.7 and 2.99 all mine to 2 leading hex zeros -> identical estimate.
        assert pow_engine.estimate_energy_cost(2.0) == pow_engine.estimate_energy_cost(2.99)
        assert pow_engine.estimate_energy_cost(2.7) == pytest.approx(16**2 * 1e-9)

    def test_integer_difficulty_unchanged(self):
        pow_engine = ProofOfWork(base_difficulty=1.0)
        assert pow_engine.estimate_energy_cost(1.0) == pytest.approx(
            16 * pow_engine.energy_per_hash
        )


class TestAnnealingZeroSteps:
    """Bug C: zero/negative max_steps must not raise."""

    def _ensemble(self):
        return ThermodynamicEnsemble(states=[_state([1.0], "n0"), _state([2.0], "n1")])

    def test_converge_zero_steps(self):
        annealer = ThermodynamicAnnealer(use_parallel_tempering=False)
        ensemble, metrics = annealer.converge(self._ensemble(), max_steps=0)
        assert metrics["steps"] == 0
        assert "final_variance" in metrics
        assert metrics["converged"] in (True, False)

    def test_converge_with_tempering_zero_steps(self):
        annealer = ThermodynamicAnnealer(use_parallel_tempering=True, n_replicas=4)
        ensemble, metrics = annealer.converge_with_tempering(self._ensemble(), max_steps=0)
        assert metrics["steps"] == 0
        assert "final_variance" in metrics


class TestMetadataSerialization:
    """Bug D: non-string metadata values must serialize into the proto map."""

    def test_genesis_metadata_serializes(self):
        pb2 = pytest.importorskip("thermodynamic_truth.network.thermo_protocol_pb2")
        from thermodynamic_truth.network.utils import stringify_metadata

        genesis = create_genesis_state(np.zeros(4), "n0")
        # Sanity: the raw metadata is exactly what used to break protobuf.
        assert genesis.metadata == {"genesis": True}

        msg = pb2.StateProposal(metadata=stringify_metadata(genesis.metadata))
        assert msg.metadata["genesis"] == "True"

    def test_stringify_handles_none_and_mixed(self):
        from thermodynamic_truth.network.utils import stringify_metadata

        assert stringify_metadata(None) == {}
        assert stringify_metadata({"hash": "abc", "n": 5, "ok": True}) == {
            "hash": "abc",
            "n": "5",
            "ok": "True",
        }
