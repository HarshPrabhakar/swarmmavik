"""Print a compact summary of a Phase 1 JSONL flight log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarm_uav.telemetry import read_events, replay_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="path to a telemetry JSONL file")
    args = parser.parse_args()
    print(json.dumps(replay_summary(read_events(args.log)), indent=2))


if __name__ == "__main__":
    main()
