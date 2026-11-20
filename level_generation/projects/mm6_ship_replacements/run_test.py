#!/usr/bin/env python3
"""Launch one of the prepared MM6 ports with private settings and saves."""
import argparse
import json
import math
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
config = json.loads((PROJECT / "source/ships.json").read_text())
maps = {Path(entry["map"]).stem: entry for entry in config["maps"]}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("map", nargs="?", choices=maps, default="oute3")
parser.add_argument("--boat", type=int, default=1, help="Boat number at that map, starting at 1")
parser.add_argument("--list", action="store_true", help="Show map keys and ship names")
args, extra = parser.parse_known_args()
if args.list:
    for key, entry in maps.items():
        print(key, "—", entry["location"], "—", ", ".join(f"{i + 1}: {s['service']}" for i, s in enumerate(entry["ships"])))
    raise SystemExit(0)
entry = maps[args.map]
if not 1 <= args.boat <= len(entry["ships"]):
    parser.error("That boat number is not present on this map")
ship = entry["ships"][args.boat - 1]
if ship["boarding_edge"]:
    x, y, z = ship["boarding_edge"]
    yaw = math.pi / 2 + ship["rotation_quarters"] * math.pi / 2
    position = [round(x - math.cos(yaw) * 360), round(y - math.sin(yaw) * 360), z + 1]
else:
    # The scenery boat has no pier or travel service; inspect it from its deck.
    position = [ship["position"][0], ship["position"][1], ship["position"][2] + 193]
    yaw = 0
command = [str(ROOT / "tools/run_game.sh"), "--isolated", "mm6_ships_" + args.map,
           "--world", "mm6", "--map", entry["map"], "--assets", str(PROJECT / "playtest/assets_dev"),
           "--position", *map(str, position), "--yaw-radians", str(yaw), "--pitch-degrees", "0",
           "--warmup", "2", "--seconds", "0", *extra]
raise SystemExit(subprocess.call(command, cwd=ROOT))
