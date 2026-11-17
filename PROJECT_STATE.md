# Project State

Updated: 2026-11-18

## Current phase

Phase 2: multi-agent basics. Phase 1 software is present, but its full exit criteria remain open pending a PX4 SITL flight/replay and a ROS 2 bridge decision.

## What exists

- Python `venv` created locally and excluded from Git.
- MAVSDK mission runner waits for simulator connection and healthy position estimates, validates route waypoints against a configured 3D bounding box, uploads a mission, requests return-to-launch, and records telemetry.
- JSONL telemetry reader and replay summary command.
- Unit tests for geofence boundaries, route rejection, and log write/read/replay behavior.
- Example simulator configuration in `config/phase1_mission.json`.
- Named 3–5 agent point-mass simulator with shared immutable snapshots and stale sequence rejection.
- Leader-following echelon controller with formation correction and Reynolds cohesion, alignment, and separation terms.
- Reproducible Phase 2 CLI and tests across 3, 4, and 5 agents for 10 seeds each.

## Phase 1 exit review

- [x] Scripted mission implementation exists.
- [x] Preflight geofence rejects routes outside configured limits.
- [x] Telemetry log replay summary exists.
- [x] Test suite passes in the created environment (7 tests).
- [ ] PX4 SITL scripted flight completes and is replayed from its log.
- [ ] ROS 2 bridge integration is selected and implemented.

Phase 1 is not complete until the remaining checks are verified. No SITL flight is claimed from this workspace. ROS 2 has not been installed or integrated; choose the target ROS 2 distribution and bridge interface before adding it.

## Phase 2 implementation review

- [x] Shared state model for named agents with monotonic sequence checks.
- [x] Stable namespace naming convention (`/agent-NN`) exposed by agent state.
- [x] Formation and Reynolds-style flocking controller for 3–5 agents.
- [x] Fixed-seed simulations show formation RMS error below 1.6 m and no pairwise collisions below 2 m across 30 runs (10 seeds × 3 swarm sizes).
- [ ] Integrate namespaced ROS 2 nodes and a transport for shared state.
- [ ] Replace the point-mass model with PX4 SITL or another dynamics-backed simulator and measure latency.

The Phase 2 simulation checks its simple kinematic model only. It does not establish stability under wind, physical vehicle dynamics, obstacles, or degraded communications.

## Next steps

1. Set up PX4 SITL on the target host, confirm its connection URI, and complete Phase 1 flight/replay review.
2. Choose the target ROS 2 distribution and bridge approach, then implement namespaced agent nodes.
3. Integrate the formation controller with simulator state and measure command latency and formation error.
4. Add link delay/loss and disturbances before considering Phase 2 complete.

## Risks and open items

- The software fence is a preflight check, not an in-flight safety barrier.
- SITL tooling and ROS 2 installation are host-specific and unavailable in this workspace.
- JSONL logs are not signed or tamper-evident.
- Hardware use requires a separate safety case, configuration review, controlled test environment, and applicable regulatory review.
