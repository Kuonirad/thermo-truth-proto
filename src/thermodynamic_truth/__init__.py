"""Thermodynamic Truth Protocol - Public API"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("thermodynamic-truth")
except PackageNotFoundError:
    # Package is not installed (running from a source checkout without
    # `pip install -e .`). Mark it explicitly rather than guess.
    __version__ = "0.0.0+unknown"

from thermodynamic_truth.core.protocol import ThermodynamicTruth

__all__ = ["ThermodynamicTruth", "__version__"]
