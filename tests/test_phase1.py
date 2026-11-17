import json

import pytest

from swarm_uav.mission import load_mission
from swarm_uav.safety import Geofence, Point
from swarm_uav.telemetry import read_events, replay_summary, write_event


def fence():
    return Geofence(10.0, 11.0, 20.0, 21.0, 0.0, 60.0)


def test_geofence_accepts_inclusive_boundary():
    assert fence().contains(Point(10.0, 20.0, 0.0))
    assert fence().contains(Point(11.0, 21.0, 60.0))


def test_geofence_rejects_route_outside_boundary():
    with pytest.raises(ValueError, match="point 2"):
        fence().validate_route([Point(10.5, 20.5, 20), Point(11.1, 20.5, 20)])


def test_geofence_rejects_empty_route():
    with pytest.raises(ValueError, match="at least one"):
        fence().validate_route([])


def test_geofence_rejects_nonfinite_point():
    assert not fence().contains(Point(float("nan"), 20.5, 10))


def test_mission_config_rejects_waypoint_outside_fence(tmp_path):
    config = {
        "geofence": {
            "min_latitude_deg": 10,
            "max_latitude_deg": 11,
            "min_longitude_deg": 20,
            "max_longitude_deg": 21,
            "min_altitude_m": 0,
            "max_altitude_m": 60,
        },
        "waypoints": [{"latitude_deg": 12, "longitude_deg": 20.5, "relative_altitude_m": 10}],
    }
    path = tmp_path / "mission.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="point 1"):
        load_mission(path)


def test_jsonl_log_can_be_replayed(tmp_path):
    log_path = tmp_path / "logs" / "flight.jsonl"
    write_event(log_path, "mission_started", {"mission_id": "demo"})
    write_event(log_path, "position", {"latitude_deg": 10.5})
    events = list(read_events(log_path))
    summary = replay_summary(events)
    assert summary["events"] == 2
    assert summary["by_type"] == {"mission_started": 1, "position": 1}
    assert json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])["data"]["mission_id"] == "demo"


def test_replay_rejects_malformed_jsonl(tmp_path):
    log_path = tmp_path / "bad.jsonl"
    log_path.write_text("{broken\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        list(read_events(log_path))
