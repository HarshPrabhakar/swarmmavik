# Secure Swarm UAV Platform

Phase 1 starts with one simulated vehicle. The first implementation uses Python and MAVSDK for mission upload and telemetry, with a small preflight fence and append-only JSON Lines logs. ROS 2 is kept out of the runtime path for now: it is a separate system dependency and there is no installed ROS distribution in this workspace. A versioned bridge can be added once the target ROS distribution and message boundary are selected.

## Learning brief and design

The script checks that every waypoint is inside a configured latitude, longitude, and relative-altitude box before connecting. It then waits for the simulator and valid global/home position estimates, uploads a short waypoint mission, arms, starts the mission, and records positions and progress. The replay utility summarizes recorded events.

This is a software preflight check, not an onboard geofence or a complete safety system. PX4's own geofence, return-to-launch, estimator and failsafe settings must be configured and checked in the simulator. Real aircraft operation is outside this phase.

An axis-aligned box is easy to inspect and test. A polygon fence supports irregular areas but needs a geometry library and careful treatment of boundaries; that is a later improvement. JSONL makes logs streamable and easy to inspect; a database is unnecessary for one vehicle at this stage.

## Setup

Python 3.10 or newer is recommended. The `venv` directory is local and ignored by Git.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

MAVSDK-Python's 3.10.2 release is pinned for the gRPC-based `mavsdk` API used here. See the [MAVSDK-Python releases](https://github.com/mavlink/MAVSDK-Python/releases) and [MAVSDK Python QuickStart](https://mavsdk.mavlink.io/main/en/python/quickstart.html). PX4 SITL setup and simulator models depend on the host OS; use the [PX4 simulation guide](https://docs.px4.io/main/en/simulation/) and start a local SITL instance before running the mission.

## Run and verify

Run the software checks:

```powershell
python -m pytest
```

Review the configured route without connecting:

```powershell
python -c "from pathlib import Path; from swarm_uav.mission import load_mission; print(load_mission(Path('config/phase1_mission.json')))"
```

With PX4 SITL already running and listening on the MAVSDK UDP address, execute the demo:

```powershell
python -m swarm_uav.mission --config config/phase1_mission.json --log logs/phase1.jsonl
```

Summarize a completed run:

```powershell
python tools/replay.py logs/phase1.jsonl
```

The supplied coordinates are a generic simulator example. Change the config for your simulator world, keeping the geofence tight around the test route. Do not use the demo config for a real aircraft.

## Phase 2: multi-agent formation simulation

The Phase 2 simulator creates 3–5 named point-mass agents, shares immutable state snapshots with monotonically increasing per-agent sequence numbers, and computes each time step from the same snapshot. Followers combine a leader-relative echelon slot with Reynolds-style cohesion, alignment, and separation terms. The fixed leader makes this first controller easy to inspect and tune; a fully leaderless flock is a more resilient alternative, but needs separate coordination and convergence analysis.

Agent names map to a stable namespace convention such as `/agent-03`. The current shared world model is an in-process Python interface; this workspace does not have ROS 2 installed, so namespaced ROS 2 nodes and DDS transport are not yet implemented. The simulation is kinematic and does not model wind, vehicle dynamics, obstacles, sensors, or link loss. Its results are software evidence only, not evidence of flight safety.

Run a five-agent simulation:

```powershell
python tools/run_phase2.py --agents 5 --seed 21
```

The CLI reports formation RMS error, minimum pairwise distance, and collision count. The automated checks run 3, 4, and 5 agents over 10 fixed seeds each; each run converges below 1.6 m formation RMS error with no pairwise separation below 2 m. Change the seed to reproduce other initial offsets.

The 2D point-mass model is deliberately simple and fast to test. A physics-based simulator with actuator limits, sensor error, and network delay is the next step before drawing conclusions about real vehicle behavior.

## Phase 1 limits

- The waypoint fence runs before upload; it does not enforce a live boundary during flight. Configure and verify PX4's native geofence and failsafes separately.
- The script requests return-to-launch after mission completion and waits for the vehicle to report landed. It does not define a robust lost-link policy or operator abort interface yet.
- Logs are local JSONL without tamper protection. Security hardening, ROS 2 integration, richer replay, and automated SITL execution remain open work.
- No PX4 SITL flight was run in this environment; only local software tests and static configuration preflight can be verified here.
