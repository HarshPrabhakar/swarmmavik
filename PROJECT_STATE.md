# Project State

Updated: 2026-11-18

## Current phase

Phase 1: single-vehicle simulation foundation.

## What exists

- Python `venv` created locally and excluded from Git.
- MAVSDK mission runner waits for simulator connection and healthy position estimates, validates route waypoints against a configured 3D bounding box, uploads a mission, requests return-to-launch, and records telemetry.
- JSONL telemetry reader and replay summary command.
- Unit tests for geofence boundaries, route rejection, and log write/read/replay behavior.
- Example simulator configuration in `config/phase1_mission.json`.

## Phase 1 exit review

- [x] Scripted mission implementation exists.
- [x] Preflight geofence rejects routes outside configured limits.
- [x] Telemetry log replay summary exists.
- [x] Test suite passes in the created environment (7 tests).
- [ ] PX4 SITL scripted flight completes and is replayed from its log.
- [ ] ROS 2 bridge integration is selected and implemented.

Phase 1 is not complete until the remaining checks are verified. No SITL flight is claimed from this workspace. ROS 2 has not been installed or integrated; choose the target ROS 2 distribution and bridge interface before adding it.

## Next steps

1. Install the pinned Python dependencies and run the tests.
2. Set up PX4 SITL on the target host and confirm its connection URI.
3. Run the demo mission, inspect the log summary, and review PX4 geofence/RTL behavior.
4. Decide the ROS 2 distribution and whether the Phase 1 bridge should publish MAVSDK telemetry or use a PX4 ROS 2 interface.

## Risks and open items

- The software fence is a preflight check, not an in-flight safety barrier.
- SITL tooling and ROS 2 installation are host-specific and unavailable in this workspace.
- JSONL logs are not signed or tamper-evident.
- Hardware use requires a separate safety case, configuration review, controlled test environment, and applicable regulatory review.
