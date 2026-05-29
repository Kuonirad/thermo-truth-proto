"""
Shared fixtures for the network/CLI integration tests.

These tests use a **real** gRPC server bound to an ephemeral localhost port and a
**real** client/channel — no mocks or fake stubs. Error paths are exercised
against a genuinely closed port so the ``grpc.RpcError`` handling runs for real.
"""

import socket

import grpc
import pytest

from thermodynamic_truth.core.protocol import ThermodynamicTruth
from thermodynamic_truth.network.server import ThermoNodeServer


def free_port() -> int:
    """Reserve an ephemeral TCP port and release it for the server to claim."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def live_server():
    """
    Start a real ThermoNodeServer on a free port and wait until it accepts
    connections. Yields the protocol instance, port, and dialable address.
    """
    protocol = ThermodynamicTruth(node_id="srv", use_parallel_tempering=False, pow_difficulty=1.0)
    port = free_port()
    server = ThermoNodeServer(protocol, port=port)
    server.start()

    address = f"localhost:{port}"
    channel = grpc.insecure_channel(address)
    try:
        grpc.channel_ready_future(channel).result(timeout=5)
    finally:
        channel.close()

    yield {"protocol": protocol, "port": port, "address": address}

    server.stop(0)


@pytest.fixture
def dead_address():
    """An address with no listener — connecting to it yields a real RpcError."""
    return f"localhost:{free_port()}"
