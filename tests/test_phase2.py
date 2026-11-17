import pytest

from swarm_uav.swarm.formation import Formation
from swarm_uav.swarm.models import AgentState, SharedWorldModel, Vec2
from swarm_uav.swarm.simulation import run_simulation


def test_shared_world_model_rejects_stale_sequence_and_keeps_snapshot_immutable():
    model = SharedWorldModel()
    fresh = AgentState("agent-01", Vec2(1, 2), Vec2(0, 0), sequence=2)
    stale = AgentState("agent-01", Vec2(8, 8), Vec2(0, 0), sequence=1)
    assert model.update(fresh)
    assert not model.update(stale)
    snapshot = model.snapshot()
    assert snapshot["agent-01"] == fresh
    with pytest.raises(TypeError):
        snapshot["agent-02"] = stale


def test_agent_state_provides_stable_ros_namespace():
    agent = AgentState("agent-03", Vec2(0, 0), Vec2(0, 0))
    assert agent.ros_namespace == "/agent-03"


def test_formation_supports_three_to_five_unique_agents():
    assert len(Formation.echelon(["a", "b", "c"]).slots_m) == 2
    assert len(Formation.echelon(["a", "b", "c", "d", "e"]).slots_m) == 4
    with pytest.raises(ValueError, match="3 to 5"):
        Formation.echelon(["a", "b"])
    with pytest.raises(ValueError, match="unique"):
        Formation.echelon(["a", "b", "b"])


@pytest.mark.parametrize("agent_count", [3, 4, 5])
def test_simulation_converges_without_collisions_for_fixed_seed_set(agent_count):
    for seed in range(10):
        result = run_simulation(agent_count=agent_count, duration_s=30, seed=seed)
        assert result.formation_rms_error_m < 1.6
        assert result.collision_count == 0
        assert result.minimum_separation_m > 2.0


def test_simulation_rejects_invalid_swarm_size_and_timing():
    with pytest.raises(ValueError, match="3 to 5"):
        run_simulation(agent_count=2)
    with pytest.raises(ValueError, match="positive"):
        run_simulation(duration_s=float("nan"))
