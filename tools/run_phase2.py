"""Run a reproducible 3–5 agent formation simulation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from swarm_uav.swarm.simulation import run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", type=int, choices=range(3, 6), default=3)
    parser.add_argument("--duration", type=float, default=60.0, help="simulation duration in seconds")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    result = run_simulation(args.agents, args.duration, seed=args.seed)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
