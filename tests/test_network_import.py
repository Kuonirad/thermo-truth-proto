"""
Regression tests for thermodynamic_truth.network package import.

Locks in the fix for the gRPC stub import bug: thermo_protocol_pb2_grpc.py
must import its sibling pb2 module via the package, not as a top-level
name. The protoc default emits `import thermo_protocol_pb2 ...` which fails
when the generated files live inside a subpackage.
"""

import importlib


class TestNetworkPackageImport:
    """The network subpackage must be importable cleanly."""

    def test_import_network_package(self):
        """Importing thermodynamic_truth.network must not raise."""
        module = importlib.import_module("thermodynamic_truth.network")
        assert hasattr(module, "ThermoNodeServer")
        assert hasattr(module, "ThermoNodeServicer")
        assert hasattr(module, "ThermoNodeClient")
        assert hasattr(module, "PeerManager")

    def test_import_pb2_grpc_stub(self):
        """The generated grpc stub must resolve its pb2 sibling via the package."""
        stub = importlib.import_module("thermodynamic_truth.network.thermo_protocol_pb2_grpc")
        pb2 = importlib.import_module("thermodynamic_truth.network.thermo_protocol_pb2")
        # The grpc stub aliases the pb2 module as thermo__protocol__pb2 (double underscore).
        # If the import had fallen back to a top-level lookup we'd never get here.
        assert stub.thermo__protocol__pb2 is pb2

    def test_server_module_imports(self):
        """The server module transitively pulls in the grpc stub — must succeed."""
        server = importlib.import_module("thermodynamic_truth.network.server")
        assert hasattr(server, "ThermoNodeServer")

    def test_client_module_imports(self):
        """The client module transitively pulls in the grpc stub — must succeed."""
        client = importlib.import_module("thermodynamic_truth.network.client")
        assert hasattr(client, "ThermoNodeClient")
