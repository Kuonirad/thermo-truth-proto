"""
Smoke tests that mirror the post-publish verification in
.github/workflows/publish.yml. Keeping these in the unit test suite
means every PR exercises the same code path that gates releases, so
a typo in a constructor kwarg (e.g. n_states vs n_replicas) cannot
ship to PyPI undetected.
"""

import numpy as np

import thermodynamic_truth
from thermodynamic_truth.core import ThermodynamicTruth


class TestPublishSmoke:
    """Mirror of the publish.yml verify-publication step."""

    def test_construct_protocol_with_published_signature(self):
        protocol = ThermodynamicTruth(node_id="test", n_replicas=4)
        assert protocol.node_id == "test"

    def test_create_genesis_returns_marked_state(self):
        protocol = ThermodynamicTruth(node_id="test", n_replicas=4)
        genesis = protocol.create_genesis(np.zeros(8))
        assert genesis.metadata.get("genesis") is True
        assert genesis.state_vector.shape == (8,)
        assert np.allclose(genesis.state_vector, 0.0)


class TestPackageVersion:
    """Verify __version__ is wired to package metadata (single source of truth)."""

    def test_version_is_a_pep440_string(self):
        v = thermodynamic_truth.__version__
        assert isinstance(v, str)
        assert v, "__version__ must not be empty"
        # In a properly installed checkout we should NOT be falling back.
        assert v != "0.0.0+unknown", (
            "Package metadata lookup failed — is the package installed " "(`pip install -e .`)?"
        )

    def test_version_matches_pyproject(self):
        """__init__.__version__ must equal the version pip resolved at install time."""
        from importlib.metadata import version

        assert thermodynamic_truth.__version__ == version("thermodynamic-truth")
