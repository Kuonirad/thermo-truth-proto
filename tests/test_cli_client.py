"""
Integration tests for the ``thermo-client`` CLI (``cli.client``).

Each command builds a real ``ThermoNodeClient`` and talks to the live gRPC server
from ``conftest.live_server``; failure cases dial a closed port. No mocks/fakes —
only ``sys.argv`` and an ``argparse.Namespace`` are constructed to invoke the
real command handlers.
"""

import argparse

import numpy as np
import pytest

from thermodynamic_truth.cli import client as cli


def _args(**kw):
    defaults = dict(
        node=None, sender_id=None, round=None, max_states=None, last_round=None, verbose=False
    )
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def _mine(protocol, vec=(1.0, 2.0, 3.0)):
    return protocol.pow_engine.create_pow_state(np.array(vec, dtype=np.float64), "peer")


# --------------------------------------------------------------------------- #
# ping / status
# --------------------------------------------------------------------------- #
class TestPingStatus:
    def test_ping_success(self, live_server, capsys):
        cli.cmd_ping(_args(node=live_server["address"]))
        assert "is alive" in capsys.readouterr().out

    def test_ping_failure_exits(self, dead_address):
        with pytest.raises(SystemExit) as e:
            cli.cmd_ping(_args(node=dead_address, sender_id="tester"))
        assert e.value.code == 1

    def test_status_success(self, live_server, capsys):
        cli.cmd_status(_args(node=live_server["address"]))
        assert "responder_id" in capsys.readouterr().out  # JSON dump

    def test_status_failure_exits(self, dead_address):
        with pytest.raises(SystemExit) as e:
            cli.cmd_status(_args(node=dead_address))
        assert e.value.code == 1


# --------------------------------------------------------------------------- #
# request-states
# --------------------------------------------------------------------------- #
class TestRequestStates:
    def test_quiet(self, live_server, capsys):
        live_server["protocol"].create_genesis(np.zeros(3))
        cli.cmd_request_states(_args(node=live_server["address"]))
        assert "Received 1 states" in capsys.readouterr().out

    def test_verbose_lists_each_state(self, live_server, capsys):
        protocol = live_server["protocol"]
        protocol.current_ensemble.add_state(_mine(protocol))
        cli.cmd_request_states(_args(node=live_server["address"], verbose=True, max_states=5))
        out = capsys.readouterr().out
        assert "Proposer: peer" in out and "Vector:" in out


# --------------------------------------------------------------------------- #
# sync
# --------------------------------------------------------------------------- #
class TestSync:
    def _seed_history(self, protocol):
        protocol.create_genesis(np.zeros(3))
        protocol.current_ensemble.add_state(_mine(protocol, (0.05, 0.0, 0.0)))
        protocol.run_consensus_round(max_annealing_steps=5, filter_byzantine=False)

    def test_quiet(self, live_server, capsys):
        self._seed_history(live_server["protocol"])
        cli.cmd_sync(_args(node=live_server["address"]))
        assert "Synchronized with" in capsys.readouterr().out

    def test_verbose_prints_history(self, live_server, capsys):
        self._seed_history(live_server["protocol"])
        cli.cmd_sync(_args(node=live_server["address"], verbose=True))
        out = capsys.readouterr().out
        assert "Consensus History" in out and "Round" in out


# --------------------------------------------------------------------------- #
# main() dispatch
# --------------------------------------------------------------------------- #
class TestMain:
    def test_no_command_prints_help_and_exits(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["thermo-client"])
        with pytest.raises(SystemExit) as e:
            cli.main()
        assert e.value.code == 1

    def test_main_ping(self, live_server, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["thermo-client", "ping", live_server["address"]])
        cli.main()
        assert "is alive" in capsys.readouterr().out

    def test_main_status(self, live_server, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["thermo-client", "status", live_server["address"]])
        cli.main()
        assert "responder_id" in capsys.readouterr().out

    def test_main_request_states(self, live_server, monkeypatch, capsys):
        live_server["protocol"].create_genesis(np.zeros(3))
        monkeypatch.setattr("sys.argv", ["thermo-client", "request-states", live_server["address"]])
        cli.main()
        assert "Received" in capsys.readouterr().out

    def test_main_sync(self, live_server, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["thermo-client", "sync", live_server["address"]])
        cli.main()
        assert "Synchronized with" in capsys.readouterr().out
