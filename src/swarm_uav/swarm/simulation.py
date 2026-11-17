"""Deterministic, point-mass multi-agent formation simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations
from math import isfinite

from swarm_uav.swarm.formation import Formation, FormationController
from swarm_uav.swarm.models import AgentState, SharedWorldModel, Vec2


@dataclass(frozen=True)
class SimulationResult:
    agents: int
    seed: int
    duration_s: float
    formation_rms_error_m: float
    minimum_separation_m: float
    collision_count: int


def run_simulation(agent_count: int = 3, duration_s: float = 60.0, dt_s: float = 0.1, seed: int = 7) -> SimulationResult:
    if not 3 <= agent_count <= 5:
        raise ValueError("simulation supports 3 to 5 agents")
    if not isfinite(duration_s) or not isfinite(dt_s) or duration_s <= 0 or dt_s <= 0:
        raise ValueError("duration and timestep must be positive")
    agent_ids = [f"agent-{index:02d}" for index in range(1, agent_count + 1)]
    formation = Formation.echelon(agent_ids)
    controller = FormationController(formation)
    random_source = random.Random(seed)
    world = SharedWorldModel()

    leader_id = agent_ids[0]
    world.update(AgentState(leader_id, Vec2(0.0, 0.0), Vec2(1.0, 0.0), sequence=1))
    for agent_id, slot in formation.slots_m.items():
        position = slot + Vec2(random_source.uniform(-2, 2), random_source.uniform(-2, 2))
        world.update(AgentState(agent_id, position, Vec2(0.0, 0.0), sequence=1))

    steps = max(1, round(duration_s / dt_s))
    for step in range(steps):
        current = world.snapshot()
        commands = {agent_id: controller.desired_velocity(agent_id, current) for agent_id in agent_ids}
        timestamp = (step + 1) * dt_s
        for agent_id in agent_ids:
            previous = current[agent_id]
            world.update(
                AgentState(
                    agent_id,
                    previous.position_m + commands[agent_id] * dt_s,
                    commands[agent_id],
                    battery_percent=previous.battery_percent,
                    health=previous.health,
                    sequence=previous.sequence + 1,
                    timestamp_s=timestamp,
                )
            )

    final = world.snapshot()
    errors = []
    for agent_id, slot in formation.slots_m.items():
        relative_position = final[agent_id].position_m - final[leader_id].position_m
        error = relative_position - slot
        errors.append(error.magnitude() ** 2)
    pair_distances = [
        (final[left].position_m - final[right].position_m).magnitude()
        for left, right in combinations(agent_ids, 2)
    ]
    return SimulationResult(
        agents=agent_count,
        seed=seed,
        duration_s=steps * dt_s,
        formation_rms_error_m=(sum(errors) / len(errors)) ** 0.5,
        minimum_separation_m=min(pair_distances),
        collision_count=sum(distance < 2.0 for distance in pair_distances),
    )
