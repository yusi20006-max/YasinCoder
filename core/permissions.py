"""Permission policy for coding-agent tool execution.

The policy is intentionally deny-by-default for side-effectful capabilities.
Read-only inspection remains available without elevation; writes, command
execution, git, network, and admin operations require explicit permission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


_CAPABILITIES = ("read", "write", "execute", "network", "git", "admin")


@dataclass(frozen=True)
class PermissionPolicy:
    read: bool = True
    write: bool = False
    execute: bool = False
    network: bool = False
    git: bool = False
    admin: bool = False

    def allows(self, capability: str) -> bool:
        if capability not in _CAPABILITIES:
            return False
        return bool(getattr(self, capability))

    @classmethod
    def from_mapping(cls, value: Mapping[str, object] | None) -> "PermissionPolicy":
        if value is None:
            return cls()
        return cls(**{name: bool(value.get(name, False)) for name in _CAPABILITIES if name in value})

    def as_dict(self) -> dict[str, bool]:
        return {name: bool(getattr(self, name)) for name in _CAPABILITIES}


class PermissionDenied(RuntimeError):
    """Raised when a tool requests a capability not granted by policy."""

    def __init__(self, capability: str):
        super().__init__(f"permission denied: {capability}")
        self.capability = capability
