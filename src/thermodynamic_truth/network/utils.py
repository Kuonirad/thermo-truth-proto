"""Serialization helpers shared by the gRPC client and server."""

from typing import Dict, Mapping, Optional


def stringify_metadata(metadata: Optional[Mapping]) -> Dict[str, str]:
    """
    Coerce a state's ``metadata`` dict into the ``map<string, string>`` shape
    required by the protobuf ``StateProposal.metadata`` field.

    ``ConsensusState.metadata`` is an arbitrary Python dict — genesis states,
    for example, carry ``{"genesis": True}`` and mined states carry a hash
    string. protobuf string maps reject non-string keys/values with a bare
    ``TypeError`` at serialization time, which previously caused
    ``RequestStates``/``SyncState``/``propose_state`` to fail for any ensemble
    that contained a genesis state. Converting everything to ``str`` keeps the
    metadata informational and serializable; values are not round-tripped back
    to their original Python types on the receiving side.

    Args:
        metadata: Source metadata mapping (may be ``None``).

    Returns:
        A new dict with all keys and values converted to ``str``.
    """
    if not metadata:
        return {}
    return {str(key): str(value) for key, value in metadata.items()}
