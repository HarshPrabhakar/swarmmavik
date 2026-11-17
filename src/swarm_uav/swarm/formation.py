"""Leader-following formation controller with Reynolds flocking terms."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Mapping

from swarm_uav.swarm.models import AgentState, Vec2


@dataclass(frozen=True)
class Formation:
    leader_id: str
    slots_m: Mapping[str, Vec2]

    def __post_init__(self) -> None:
        if not self.leader_id:
            raise ValueError("leader ID must be non-empty")
        if self.leader_id in self.slots_m:
            raise ValueError("leader cannot also have a follower slot")
        if any(not agent_id for agent_id in self.slots_m):
            raise ValueError("formation agent names must be non-empty")

    @classmethod
    def echelon(cls, agent_ids: list[str], spacing_m: float = 5.0) -> Formation:
        """Create a compact trailing echelon for 3–5 agents, leader first."""
        if not 3 <= len(agent_ids) <= 5:
            raise ValueError("Phase 2 formation supports 3 to 5 agents")
        if len(set(agent_ids)) != len(agent_ids) or not all(agent_ids):
            raise ValueError("agent IDs must be unique and non-empty")
        if spacing_m < 3:
            raise ValueError("spacing must be at least 3 m for this demo")
        offsets = [
            Vec2(-spacing_m, -spacing_m),
            Vec2(-spacing_m, spacing_m),
            Vec2(-2 * spacing_m, -spacing_m),
            Vec2(-2 * spacing_m, spacing_m),
        ]
        return cls(agent_ids[0], dict(zip(agent_ids[1:], offsets)))


@dataclass(frozen=True)
class FlockingGains:
    formation: float = 0.65
    cohesion: float = 0.06
    alignment: float = 0.35
    separation: float = 1.2
    neighbor_radius_m: float = 20.0
    separation_radius_m: float = 3.0
    max_speed_m_s: float = 2.0
    leader_speed_m_s: float = 1.0

    def __post_init__(self) -> None:
        values = (self.formation, self.cohesion, self.alignment, self.separation)
        if not all(isfinite(value) and value >= 0 for value in values):
            raise ValueError("flocking weights must be finite and non-negative")
        limits = (self.neighbor_radius_m, self.separation_radius_m, self.max_speed_m_s, self.leader_speed_m_s)
        if not all(isfinite(value) and value > 0 for value in limits):
            raise ValueError("radii and speed limits must be finite and positive")
        if self.separation_radius_m > self.neighbor_radius_m:
            raise ValueError("separation radius cannot exceed neighbor radius")


class FormationController:
    def __init__(self, formation: Formation, gains: FlockingGains = FlockingGains()) -> None:
        self.formation = formation
        self.gains = gains

    def desired_velocity(self, agent_id: str, world: Mapping[str, AgentState]) -> Vec2:
        if agent_id not in world:
            raise KeyError(f"agent {agent_id!r} is missing from shared state")
        state = world[agent_id]
        if agent_id == self.formation.leader_id:
            return Vec2(self.gains.leader_speed_m_s, 0.0)
        if agent_id not in self.formation.slots_m:
            raise ValueError(f"agent {agent_id!r} has no formation slot")
        if self.formation.leader_id not in world:
            raise ValueError("leader state is missing from shared state")

        leader = world[self.formation.leader_id]
        target = leader.position_m + self.formation.slots_m[agent_id]
        neighbors = [
            neighbor
            for neighbor_id, neighbor in world.items()
            if neighbor_id != agent_id
            and hypot(neighbor.position_m.x - state.position_m.x, neighbor.position_m.y - state.position_m.y)
            <= self.gains.neighbor_radius_m
        ]

        cohesion = Vec2(0.0, 0.0)
        alignment = Vec2(0.0, 0.0)
        separation = Vec2(0.0, 0.0)
        if neighbors:
            center = Vec2(
                sum(neighbor.position_m.x for neighbor in neighbors) / len(neighbors),
                sum(neighbor.position_m.y for neighbor in neighbors) / len(neighbors),
            )
            average_velocity = Vec2(
                sum(neighbor.velocity_m_s.x for neighbor in neighbors) / len(neighbors),
                sum(neighbor.velocity_m_s.y for neighbor in neighbors) / len(neighbors),
            )
            cohesion = center - state.position_m
            alignment = average_velocity - state.velocity_m_s
            for neighbor in neighbors:
                delta = state.position_m - neighbor.position_m
                distance = delta.magnitude()
                if 0 < distance < self.gains.separation_radius_m:
                    separation = separation + delta * ((self.gains.separation_radius_m - distance) / distance)

        command = (
            (target - state.position_m) * self.gains.formation
            + cohesion * self.gains.cohesion
            + alignment * self.gains.alignment
            + separation * self.gains.separation
        )
        return command.limited(self.gains.max_speed_m_s)
