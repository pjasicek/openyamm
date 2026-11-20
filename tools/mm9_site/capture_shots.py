#!/usr/bin/env python3
"""In-game screenshots for the MM9 guide: each map's arrival view and the key NPCs (story quest givers, promoters,
ship and coach docks), one isolated game boot per map with an engine screenshot tour (tools/RUN_GAME.md).

Run after build_site.py (it reads output/mm9_site/data/guide.js for the key NPCs); writes PNGs to
output/mm9_site_shots/<map>/ and a manifest. build_site.py then turns them into img/shots/*.webp.

    python3 tools/mm9_site/capture_shots.py [--maps sturmfordcity,anskramkeep] [--jobs 3]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "assets_dev/worlds/mm9"
OUT = ROOT / "output/mm9_site_shots"

NPC_DISTANCE = 230.0  # party-foot distance in front of the NPC; the party eye looks at the NPC's face from there
YAW_UNITS = 2048.0


def key_npcs(guide: dict) -> dict[str, set[str]]:
    wanted: dict[str, set[str]] = {}
    for quest in guide["quests"]:
        if quest["cat"] == "main":
            for giver in quest["givers"]:
                wanted.setdefault(giver["map"], set()).add(giver["poi"])
    for promotion in guide["promotions"]:
        for at in promotion["at"]:
            if at["poi"].startswith("a"):
                wanted.setdefault(at["map"], set()).add(at["poi"])
    for schedule in guide["travel"]["schedules"]:
        for at in schedule["at"]:
            wanted.setdefault(at["map"], set()).add(at["poi"])
    return wanted


def tour_for(map_id: str, npc_pois: set[str], out_dir: Path) -> str:
    scene = json.loads((WORLD / "maps" / f"{map_id}.scene.yml").read_text())
    lines = [f"output_dir: {out_dir}", "settle_seconds: 2.5", "exit: true", "shots:"]
    start = scene["party_start_points"][0]
    x, y, z = start["position"]
    lines += [
        "  - name: arrival",
        f"    position: [{x}, {y}, {z}]",
        f"    yaw: {math.radians(start['direction_degrees']):.4f}",
        "    pitch: -0.04",
        '    time: "11:00"',
        "    settle_seconds: 4",
    ]
    actors = {f"a{a['actor_index']}": a for a in scene["initial_state"]["actors"]}
    for poi in sorted(npc_pois):
        actor = actors.get(poi)
        if actor is None:
            continue
        facing = actor.get("initial_yaw_units", 0) / YAW_UNITS * 2 * math.pi
        pos = actor["position"]
        cx = pos["x"] + math.cos(facing) * NPC_DISTANCE
        cy = pos["y"] + math.sin(facing) * NPC_DISTANCE
        lines += [
            f"  - name: {poi}",
            f"    position: [{cx:.0f}, {cy:.0f}, {pos['z']}]",
            f"    yaw: {(facing + math.pi) % (2 * math.pi):.4f}",
            "    pitch: -0.08",
        ]
    return "\n".join(lines) + "\n"


def capture(map_id: str, npc_pois: set[str]) -> tuple[str, int]:
    out_dir = OUT / map_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    tour = out_dir / "tour.yml"
    tour.write_text(tour_for(map_id, npc_pois, out_dir))
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    command = [str(ROOT / "tools/run_game.sh"), "--isolated", f"mm9guide_{map_id}", "--world", "mm9", "--map",
               f"{map_id}.blv", "--warmup", "3", "--seconds", "120", "--set",
               f"debug.screenshot_tour_path={tour}"]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    shots = sorted(out_dir.glob("*.png"))
    if result.returncode != 0:
        print(f"{map_id}: run exited {result.returncode}\n{result.stderr[-800:]}", file=sys.stderr)
    return map_id, len(shots)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--maps", help="comma-separated map ids (default: all)")
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    guide_js = (ROOT / "output/mm9_site/data/guide.js").read_text()
    guide = json.loads(guide_js[guide_js.index("{"):guide_js.rindex("}") + 1])
    npcs = key_npcs(guide)
    map_ids = args.maps.split(",") if args.maps else [m["id"] for m in guide["maps"]]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for map_id, count in pool.map(lambda m: capture(m, npcs.get(m, set())), map_ids):
            print(f"{map_id}: {count} shots", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
