"""
Integration tests for ``network.client`` against a real gRPC server.

A live ``ThermoNodeServer`` (see ``conftest.live_server``) handles every request;
the client talks to it over an actual TCP channel. Error paths dial a genuinely
closed port so the real ``grpc.RpcError`` handling executes. No mocks/fakes.
"""

import numpy as np

from thermodynamic_truth.network.client import ThermoNodeClient, PeerManager
from thermodynamic_truth.core.state import ConsensusState


def _mined_state(protocol, vec=(1.0, 2.0, 3.0)):
    """Produce a state carrying a valid PoW the server will accept."""
    return protocol.pow_engine.create_pow_state(np.array(vec, dtype=np.float64), "peer")


# --------------------------------------------------------------------------- #
# Connection lifecycle
# --------------------------------------------------------------------------- #
class TestConnectionLifecycle:
    def test_connect_then_close(self, live_server):
        c = ThermoNodeClient(live_server["address"])
        c.connect()
        assert c.stub is not None
        c.close()

    def test_close_without_connect_is_noop(self, dead_address):
        c = ThermoNodeClient(dead_address)
        c.close()  # channel is None -> branch skipped, must not raise
        assert c.channel is None

    def test_lazy_connect_on_first_call(self, live_server):
        c = ThermoNodeClient(live_server["address"])
        assert c.stub is None
        status = c.ping("me")  # establishes the connection on demand
        assert c.stub is not None
        assert status["responder_id"] == "srv"
        c.close()


# --------------------------------------------------------------------------- #
# RPC success paths (real server)
# --------------------------------------------------------------------------- #
class TestRpcAgainstLiveServer:
    def test_ping(self, live_server):
        c = ThermoNodeClient(live_server["address"])
        status = c.ping("me")
        assert status["responder_id"] == "srv"
        assert status["ensemble_size"] == 0
        c.close()

    def test_propose_state_is_accepted_and_grows_ensemble(self, live_server):
        protocol = live_server["protocol"]
        c = ThermoNodeClient(live_server["address"])
        accepted, info = c.propose_state(_mined_state(protocol))
        assert accepted is True
        assert info["ensemble_size"] == 1
        # The server really added it.
        assert len(protocol.current_ensemble.states) == 1
        c.close()

    def test_request_states_roundtrip_including_genesis(self, live_server):
        protocol = live_server["protocol"]
        protocol.create_genesis(np.zeros(4))  # genesis metadata {"genesis": True}
        c = ThermoNodeClient(live_server["address"])
        states = c.request_states("req", round_number=0, max_states=10)
        assert len(states) == 1
        assert isinstance(states[0], ConsensusState)
        assert states[0].metadata["genesis"] == "True"  # serialized over the wire
        c.close()

    def test_announce_consensus(self, live_server):
        c = ThermoNodeClient(live_server["address"])
        ok = c.announce_consensus(1, np.zeros(3), 0.01, 0.02, 0.0, "me")
        assert ok is True
        c.close()

    def test_sync_state_returns_history_and_pending(self, live_server):
        protocol = live_server["protocol"]
        # Populate a real consensus history entry and a pending (genesis) state.
        protocol.create_genesis(np.zeros(3))
        protocol.current_ensemble.add_state(_mined_state(protocol, (0.05, 0.0, 0.0)))
        protocol.run_consensus_round(max_annealing_steps=5, filter_byzantine=False)
        protocol.create_genesis(np.zeros(3))  # leave a pending state in the ensemble

        c = ThermoNodeClient(live_server["address"])
        current_round, history, pending = c.sync_state("req", last_known_round=0)
        assert current_round >= 1
        assert len(history) >= 1
        assert history[0]["announcer_id"] == "srv"
        assert len(pending) >= 1
        c.close()


# --------------------------------------------------------------------------- #
# RPC error paths (real closed port)
# --------------------------------------------------------------------------- #
class TestRpcErrors:
    def _client(self, dead_address):
        return ThermoNodeClient(dead_address, timeout=1)

    def test_propose_state_error(self, dead_address):
        ok, info = self._client(dead_address).propose_state(
            ConsensusState(np.array([1.0]), 0.0, 0.0, "me", 0, 1.0)
        )
        assert ok is False and "RPC error" in info["message"]

    def test_request_states_error(self, dead_address):
        assert self._client(dead_address).request_states("req", 0) == []

    def test_announce_consensus_error(self, dead_address):
        assert (
            self._client(dead_address).announce_consensus(1, np.zeros(2), 0.1, 0.2, 0.0, "me")
            is False
        )

    def test_ping_error(self, dead_address):
        assert self._client(dead_address).ping("me") is None

    def test_sync_state_error(self, dead_address):
        assert self._client(dead_address).sync_state("req", 0) == (0, [], [])


# --------------------------------------------------------------------------- #
# PeerManager against a real peer
# --------------------------------------------------------------------------- #
class TestPeerManager:
    def test_add_peer_idempotent(self, live_server):
        pm = PeerManager()
        a = pm.add_peer(live_server["address"])
        b = pm.add_peer(live_server["address"])
        assert a is b and set(pm.peers) == {live_server["address"]}
        pm.close_all()

    def test_remove_peer_present_and_absent(self, live_server):
        pm = PeerManager()
        pm.add_peer(live_server["address"])
        pm.remove_peer(live_server["address"])
        assert live_server["address"] not in pm.peers
        pm.remove_peer("localhost:9")  # absent -> no-op

    def test_broadcast_state(self, live_server):
        protocol = live_server["protocol"]
        pm = PeerManager()
        pm.add_peer(live_server["address"])
        results = pm.broadcast_state(_mined_state(protocol))
        assert results == {live_server["address"]: True}
        pm.close_all()

    def test_broadcast_consensus(self, live_server):
        pm = PeerManager()
        pm.add_peer(live_server["address"])
        results = pm.broadcast_consensus(1, np.zeros(3), 0.1, 0.2, 0.0, "me")
        assert results == {live_server["address"]: True}
        pm.close_all()

    def test_ping_all(self, live_server):
        pm = PeerManager()
        pm.add_peer(live_server["address"])
        results = pm.ping_all("me")
        assert results[live_server["address"]]["responder_id"] == "srv"
        pm.close_all()

    def test_close_all(self, live_server):
        pm = PeerManager()
        pm.add_peer(live_server["address"])
        pm.close_all()
        assert pm.peers == {}
