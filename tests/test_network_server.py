"""
Tests for the gRPC servicer logic (``network.server.ThermoNodeServicer``).

The servicer methods are exercised directly with constructed protobuf messages
and a ``None`` context — they never touch the context, so no real gRPC channel
or socket is required. This covers the request-handling / (de)serialization
logic, including the genesis-metadata serialization fix.
"""

import numpy as np
import pytest

from thermodynamic_truth.core.protocol import ThermodynamicTruth
from thermodynamic_truth.network import thermo_protocol_pb2 as pb2
from thermodynamic_truth.network.server import ThermoNodeServicer


@pytest.fixture
def protocol():
    return ThermodynamicTruth(node_id="srv", use_parallel_tempering=False, pow_difficulty=1.0)


@pytest.fixture
def servicer(protocol):
    return ThermoNodeServicer(protocol)


def _valid_proposal(protocol, vec):
    """Mine a real PoW state and pack it into a StateProposal message."""
    state = protocol.pow_engine.create_pow_state(np.array(vec, dtype=np.float64), "peer")
    return pb2.StateProposal(
        state_vector=state.state_vector.tobytes(),
        energy=state.energy,
        timestamp=state.timestamp,
        proposer_id=state.proposer_id,
        nonce=state.nonce,
        difficulty=state.difficulty,
    )


class TestProposeState:
    def test_accepts_valid_pow(self, servicer, protocol):
        resp = servicer.ProposeState(_valid_proposal(protocol, [1.0, 2.0, 3.0]), context=None)
        assert resp.accepted is True
        assert resp.ensemble_size == 1

    def test_rejects_invalid_pow(self, servicer, protocol):
        bad = pb2.StateProposal(
            state_vector=np.array([1.0]).tobytes(),
            energy=1.0,
            timestamp=0.0,
            proposer_id="liar",
            nonce=0,
            difficulty=8.0,  # 8 leading zeros that the all-zero nonce won't satisfy
        )
        resp = servicer.ProposeState(bad, context=None)
        assert resp.accepted is False

    def test_malformed_request_is_handled(self, servicer):
        # Odd byte length cannot be reinterpreted as float64 -> handled, not raised.
        bad = pb2.StateProposal(state_vector=b"\x01\x02\x03", proposer_id="x", difficulty=1.0)
        resp = servicer.ProposeState(bad, context=None)
        assert resp.accepted is False
        assert "Error" in resp.message or resp.message


class TestRequestStatesWithGenesis:
    def test_genesis_state_is_serialized(self, servicer, protocol):
        # Genesis metadata is {"genesis": True} — the value that used to break
        # protobuf map<string,string> serialization (Bug D).
        protocol.create_genesis(np.zeros(4))
        bundle = servicer.RequestStates(pb2.StateRequest(max_states=0), context=None)
        assert len(bundle.states) == 1
        assert bundle.states[0].metadata["genesis"] == "True"

    def test_max_states_limit(self, servicer, protocol):
        for i in range(5):
            servicer.ProposeState(_valid_proposal(protocol, [float(i)]), context=None)
        bundle = servicer.RequestStates(pb2.StateRequest(max_states=2), context=None)
        assert len(bundle.states) == 2


class TestPingAndAnnounce:
    def test_ping_reports_status(self, servicer):
        resp = servicer.Ping(pb2.PingRequest(sender_id="c", timestamp=123.0), context=None)
        assert resp.responder_id == "srv"
        assert resp.timestamp == 123.0

    def test_announce_consensus_acknowledged(self, servicer):
        ann = pb2.ConsensusAnnouncement(
            round_number=1,
            consensus_state=np.zeros(3).tobytes(),
            final_variance=0.01,
            final_temperature=0.02,
            final_entropy=0.0,
            announcer_id="peer",
        )
        resp = servicer.AnnounceConsensus(ann, context=None)
        assert resp.acknowledged is True


class TestSyncState:
    def test_sync_returns_pending_states(self, servicer, protocol):
        protocol.create_genesis(np.zeros(4))  # genesis metadata must serialize here too
        resp = servicer.SyncState(
            pb2.SyncRequest(requester_id="c", last_known_round=0), context=None
        )
        assert len(resp.pending_states) == 1
        assert resp.pending_states[0].metadata["genesis"] == "True"
