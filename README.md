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

## Phase 1 limits

- The waypoint fence runs before upload; it does not enforce a live boundary during flight. Configure and verify PX4's native geofence and failsafes separately.
- The script requests return-to-launch after mission completion and waits for the vehicle to report landed. It does not define a robust lost-link policy or operator abort interface yet.
- Logs are local JSONL without tamper protection. Security hardening, ROS 2 integration, richer replay, and automated SITL execution remain open work.
- No PX4 SITL flight was run in this environment; only local software tests and static configuration preflight can be verified here.
