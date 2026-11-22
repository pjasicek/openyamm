#!/usr/bin/env python3
"""In-game screenshots for the Xeen guide: each map's arrival view and the key people placed outdoors (story quest
givers, promoters), one isolated, minimised game boot per map with an engine screenshot tour (tools/RUN_GAME.md), with
the Xeen build (build-xeen/game/openyamm unless $OPENYAMM_GAME_BINARY says otherwise). The MM9 guide's
capture_shots.py, on the Xeen world's scenes: an outdoor map's arrival is its `party start` entity, an indoor map's its
first party start point. People in houses have no 3D view and get no picture.

Run after build_site.py (it reads output/xeen_site/data/guide.js); writes PNGs to output/xeen_site_shots/<map>/.
build_site.py then turns them into img/shots/*.webp.

    python3 tools/xeen_site/capture_shots.py [--maps xeen_x1,xeen_xd01] [--jobs 2]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "assets_dev/worlds/xeen"
OUT = ROOT / "output/xeen_site_shots"

sys.path.insert(0, str(ROOT / "tools/maw_site"))
import dungeon_plans  # noqa: E402

dungeon_plans.WORLD_IDS = ("xeen",)

_spec = importlib.util.spec_from_file_location("mm9_capture_shots", ROOT / "tools/mm9_site/capture_shots.py")
mm9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mm9)


def load_scene(map_id: str) -> dict:
    text = (WORLD / "maps" / f"{map_id}.scene.yml").read_text()
    return json.loads(text) if text.lstrip().startswith("{") else yaml.load(text, Loader=yaml.CSafeLoader)


def arrival(scene: dict) -> tuple[list[float], float] | None:
    """The party's start (x, y, z) and yaw in radians."""
    points = scene.get("party_start_points") or []
    if points:
        return list(points[0]["position"]), math.radians(points[0].get("direction_degrees", 0))
    for entity in scene.get("entities") or []:
        if entity.get("name") == "party start":
            pos = entity["position"]
            return [pos["x"], pos["y"], pos["z"]], entity.get("facing", 0) / mm9.YAW_UNITS * 2 * math.pi
    return None


def sight(walls: list[tuple[float, float, float, float]], x: float, y: float, yaw: float, cap: float = 8000) -> float:
    """How far the eye sees from (x, y) along yaw before a wall (2D footprints of the walls at eye height)."""
    dx, dy = math.cos(yaw), math.sin(yaw)
    best = cap
    for ax, ay, bx, by in walls:
        ex, ey = bx - ax, by - ay
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-9:
            continue
        t = ((ax - x) * ey - (ay - y) * ex) / denom   # along the ray
        u = ((ax - x) * dy - (ay - y) * dx) / denom   # along the wall
        if 1 < t < best and 0 <= u <= 1:
            best = t
    return best


def open_view(map_file: str, position: list[float], yaw: float) -> tuple[list[float], float]:
    """open_yaw, and in a small entry room (the view ends within 1,000) the camera steps back to the wall behind, so
    the shot shows the room instead of the door ahead."""
    yaw = open_yaw(map_file, position, yaw)
    walls = arrival_walls(map_file, position)
    x, y, z = position
    if walls and sight(walls, x, y, yaw) < 1000:
        back = sight(walls, x, y, yaw + math.pi, cap=1200) - 96
        if back > 64:
            return [x - math.cos(yaw) * back, y - math.sin(yaw) * back, z], yaw
    return position, yaw


def arrival_walls(map_file: str, position: list[float]) -> list[tuple[float, float, float, float]]:
    payload = dungeon_plans.load(map_file)
    if payload is None:
        return []
    eye = position[2] + 150
    walls = []
    for face in payload["faces"]:
        if face["facet_type"] != dungeon_plans.WALL or face["is_portal"] or \
                face["attributes"] & (dungeon_plans.PORTAL | dungeon_plans.INVISIBLE):
            continue
        points = dungeon_plans.face_points(payload, face)
        if len(points) < 2 or not min(p[2] for p in points) <= eye <= max(p[2] for p in points):
            continue
        a, b = max(((p, q) for p in points for q in points), key=lambda pq: (pq[0][0] - pq[1][0]) ** 2 +
                   (pq[0][1] - pq[1][1]) ** 2)
        walls.append((a[0], a[1], b[0], b[1]))
    return walls


def open_yaw(map_file: str, position: list[float], yaw: float) -> float:
    """An indoor arrival's view: its own facing unless that faces a door or a wall close by (many arrivals stand just
    inside the entrance, looking at it); then the facing of the longest clear view, of sixteen."""
    walls = arrival_walls(map_file, position)
    if not walls:
        return yaw
    x, y, z = position
    own = sight(walls, x, y, yaw)
    if own >= 1500:
        return yaw
    choices = [yaw + k * math.pi / 8 for k in range(16)]
    best = max(choices, key=lambda c: sight(walls, x, y, c))
    return best if sight(walls, x, y, best) > own * 1.5 else yaw


def tour_for(map_id: str, npc_pois: set[str], out_dir: Path, map_file: str = "") -> str:
    scene = load_scene(map_id)
    lines = [f"output_dir: {out_dir}", "settle_seconds: 2.5", "exit: true", "shots:"]
    start = arrival(scene)
    if start is not None:
        (x, y, z), yaw = start
        if map_file.endswith(".blv"):
            (x, y, z), yaw = open_view(map_file, [x, y, z], yaw)
        lines += ["  - name: arrival", f"    position: [{x}, {y}, {z}]", f"    yaw: {yaw:.4f}", "    pitch: -0.04",
                  '    time: "11:00"', "    settle_seconds: 4"]
    actors = {f"a{a['actor_index']}": a for a in scene["initial_state"]["actors"]}
    for poi in sorted(npc_pois):
        actor = actors.get(poi)
        if actor is None:
            continue
        facing = actor.get("initial_yaw_units", 0) / mm9.YAW_UNITS * 2 * math.pi
        pos = actor["position"]
        cx = pos["x"] + math.cos(facing) * mm9.NPC_DISTANCE
        cy = pos["y"] + math.sin(facing) * mm9.NPC_DISTANCE
        lines += [f"  - name: {poi}", f"    position: [{cx:.0f}, {cy:.0f}, {pos['z']}]",
                  f"    yaw: {(facing + math.pi) % (2 * math.pi):.4f}", "    pitch: -0.08"]
    return "\n".join(lines) + "\n"


def capture(map_id: str, file_name: str, npc_pois: set[str]) -> tuple[str, int]:
    out_dir = OUT / map_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    tour = out_dir / "tour.yml"
    tour.write_text(tour_for(map_id, npc_pois, out_dir, file_name))
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    env.setdefault("OPENYAMM_GAME_BINARY", str(ROOT / "build-xeen/game/openyamm"))
    command = [str(ROOT / "tools/run_game.sh"), "--isolated", f"xeenguide_{map_id}", "--world", "xeen", "--map",
               file_name, "--warmup", "3", "--seconds", "120", "--set", f"debug.screenshot_tour_path={tour}"]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"{map_id}: run exited {result.returncode}\n{result.stderr[-800:]}", file=sys.stderr)
    return map_id, len(list(out_dir.glob("*.png")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--maps", help="comma-separated map ids (default: all)")
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    guide_js = (ROOT / "output/xeen_site/data/guide.js").read_text()
    guide = json.loads(guide_js[guide_js.index("{"):guide_js.rindex("}") + 1])
    npcs = mm9.key_npcs(guide)
    maps_yml = yaml.safe_load((WORLD / "source/maps.yml").read_text())["maps"]
    files = {m["stem"].rsplit(".", 1)[0]: m["stem"] for m in maps_yml}
    map_ids = args.maps.split(",") if args.maps else [m["id"] for m in guide["maps"]]
    with ThreadPoolExecutor(max_workers=min(args.jobs, 2)) as pool:
        for map_id, count in pool.map(lambda m: capture(m, files[m], npcs.get(m, set())), map_ids):
            print(f"{map_id}: {count} shots", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
