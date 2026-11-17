"""Small, transport-neutral state model for named simulated agents."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __post_init__(self) -> None:
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("vector components must be finite")

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def magnitude(self) -> float:
        return hypot(self.x, self.y)

    def limited(self, maximum: float) -> Vec2:
        magnitude = self.magnitude()
        if magnitude <= maximum or magnitude == 0:
            return self
        return self * (maximum / magnitude)


@dataclass(frozen=True)
class AgentState:
    agent_id: str
    position_m: Vec2
    velocity_m_s: Vec2
    battery_percent: float = 100.0
    health: str = "ok"
    sequence: int = 0
    timestamp_s: float = 0.0

    def __post_init__(self) -> None:
        if not self.agent_id or "/" in self.agent_id:
            raise ValueError("agent_id must be a non-empty name without slashes")
        values = (
            self.position_m.x,
            self.position_m.y,
            self.velocity_m_s.x,
            self.velocity_m_s.y,
            self.battery_percent,
            self.timestamp_s,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("agent state values must be finite")
        if not 0 <= self.battery_percent <= 100:
            raise ValueError("battery_percent must be in [0, 100]")
        if self.sequence < 0 or self.timestamp_s < 0:
            raise ValueError("sequence and timestamp must be non-negative")

    @property
    def ros_namespace(self) -> str:
        """Stable namespace convention for a future ROS 2 transport adapter."""
        return f"/{self.agent_id}"


class SharedWorldModel:
    """In-process shared state with monotonic per-agent sequence protection."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentState] = {}

    def update(self, state: AgentState) -> bool:
        current = self._agents.get(state.agent_id)
        if current is not None and state.sequence <= current.sequence:
            return False
        self._agents[state.agent_id] = state
        return True

    def snapshot(self) -> Mapping[str, AgentState]:
        return MappingProxyType(self._agents.copy())

    def __len__(self) -> int:
        return len(self._agents)
