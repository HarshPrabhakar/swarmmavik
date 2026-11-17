"""Run a small, preflight-checked MAVSDK mission against a simulator."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

from swarm_uav.safety import Geofence, Point
from swarm_uav.telemetry import write_event


def load_mission(path: Path) -> tuple[Geofence, list[dict[str, Any]], float]:
    config = json.loads(path.read_text(encoding="utf-8"))
    fence = Geofence(**config["geofence"])
    waypoints = config["waypoints"]
    speed = float(config.get("speed_m_s", 3.0))
    if not 0 < speed <= 5:
        raise ValueError("demo mission speed must be greater than 0 and no more than 5 m/s")
    points = [Point(w["latitude_deg"], w["longitude_deg"], w["relative_altitude_m"]) for w in waypoints]
    fence.validate_route(points)
    return fence, waypoints, speed


async def _wait_for_connection(drone: System, timeout_s: float = 30.0) -> None:
    async def wait() -> None:
        async for state in drone.core.connection_state():
            if state.is_connected:
                return
    await asyncio.wait_for(wait(), timeout=timeout_s)


async def _wait_for_position(drone: System, timeout_s: float = 60.0) -> None:
    async def wait() -> None:
        async for health in drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                return
    await asyncio.wait_for(wait(), timeout=timeout_s)


async def _record_position(drone: System, log_path: Path, stop: asyncio.Event) -> None:
    async for position in drone.telemetry.position():
        if stop.is_set():
            return
        write_event(
            log_path,
            "position",
            {
                "latitude_deg": position.latitude_deg,
                "longitude_deg": position.longitude_deg,
                "absolute_altitude_m": position.absolute_altitude_m,
                "relative_altitude_m": position.relative_altitude_m,
            },
        )


async def _record_progress(drone: System, log_path: Path) -> None:
    async for progress in drone.mission.mission_progress():
        write_event(log_path, "mission_progress", {"current": progress.current, "total": progress.total})
        if progress.total and progress.current >= progress.total:
            return


async def _wait_for_landing(drone: System, timeout_s: float = 900.0) -> None:
    async def wait() -> None:
        was_in_air = False
        async for in_air in drone.telemetry.in_air():
            was_in_air = was_in_air or in_air
            if was_in_air and not in_air:
                return
    await asyncio.wait_for(wait(), timeout=timeout_s)


async def run(config_path: Path, log_path: Path, address: str) -> None:
    _, waypoints, speed = load_mission(config_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_event(log_path, "preflight_passed", {"waypoint_count": len(waypoints), "speed_m_s": speed})

    drone = System()
    await drone.connect(system_address=address)
    await _wait_for_connection(drone)
    write_event(log_path, "connected", {"system_address": address})
    await _wait_for_position(drone)
    write_event(log_path, "position_health_ok", {})

    items = [
        MissionItem(
            point["latitude_deg"],
            point["longitude_deg"],
            point["relative_altitude_m"],
            speed,
            True,
            float("nan"),
            float("nan"),
            MissionItem.CameraAction.NONE,
        )
        for point in waypoints
    ]
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(MissionPlan(items))
    write_event(log_path, "mission_uploaded", {"waypoint_count": len(items)})
    await drone.action.arm()
    write_event(log_path, "armed", {})
    await drone.mission.start_mission()
    write_event(log_path, "mission_started", {})

    stop = asyncio.Event()
    position_task = asyncio.create_task(_record_position(drone, log_path, stop))
    progress_task = asyncio.create_task(_record_progress(drone, log_path))
    try:
        await _wait_for_landing(drone)
    finally:
        stop.set()
        for task in (position_task, progress_task):
            task.cancel()
        await asyncio.gather(position_task, progress_task, return_exceptions=True)
    write_event(log_path, "mission_finished", {})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/phase1_mission.json"))
    parser.add_argument("--log", type=Path, default=Path("logs/phase1.jsonl"))
    parser.add_argument("--address", default="udpin://0.0.0.0:14540", help="MAVSDK connection URI")
    args = parser.parse_args()
    # Fail the safety preflight before opening a vehicle connection.
    load_mission(args.config)
    asyncio.run(run(args.config, args.log, args.address))


if __name__ == "__main__":
    main()
