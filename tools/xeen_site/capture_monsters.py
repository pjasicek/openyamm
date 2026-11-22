#!/usr/bin/env python3
"""Portraits for the Xeen guide's bestiary: each monster alone in the great hall of the Tower of High Magic (XD-11's
4,096 by 3,328 room, an AI arena that clears the map's actors and spawns only it, not hostile), photographed from the
front by a one-shot screenshot tour, the HUD cropped away and the crosshair painted out (the MM9 guide's
capture_monsters.py on a Xeen map). The Warzone (XD-20) would suit better, but a map that forbids saving cannot start
an isolated run.
One isolated, minimised game boot per monster with the Xeen build (build-xeen/game/openyamm unless
$OPENYAMM_GAME_BINARY says otherwise).

Run after build_site.py (reads output/xeen_site/data/guide.js for the monsters); writes output/xeen_site_monsters/
<id>.png. build_site.py then turns them into img/monsters/<id>.webp.

    python3 tools/xeen_site/capture_monsters.py [--ids 11010,11011] [--jobs 2] [--missing]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "assets_dev/worlds/xeen"
OUT = ROOT / "output/xeen_site_monsters"
WORK = OUT / "work"

_spec = importlib.util.spec_from_file_location("mm9_capture_monsters", ROOT / "tools/mm9_site/capture_monsters.py")
mm9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mm9)

MAP = "xeen_xd11.blv"
CENTRE = (0.0, -384.0, 2561.0)  # the hall's floor: x -2048..2048, y -2048..1280, z 2560
HALL_Y = (-2048.0, 1280.0)
EYE = 160.0  # the indoor party's eye height (Xeen's world.yml sets none)
CROP = mm9.CROP
# The crop's middle lies 0.42 of the frame height down (above the frame's middle): the camera looks this much further
# down than at the monster's middle, which puts that middle in the crop's middle (60 degree vertical field of view).
CROP_AIM = math.atan((0.5 - (CROP[1] + CROP[3]) / 2) * 2 * math.tan(math.radians(30)))
# Models whose static bounds hold outspread wings (the bind pose) that the idle pose folds up: the dragons filled about
# half the portrait's height at the bounds' distance, so the camera comes this much closer (less for the dark dragons,
# whose raised wings reach above their bounds, and the bone dragons, which stand lower than their collision box).
CLOSER = {"xeen_cdr1.glb": 0.72, "xeen_m492.glb": 0.85, "xeen_m616.glb": 0.82}


def model_sizes() -> dict[int, tuple[float, float, float, str]]:
    """Each monster's drawn size (half its widest horizontal side, height, depth along its facing), from its 3D model's
    static bounds at the binding's scale, and the model's file name: a model can be far larger than its collision box
    (the swamp things' treant at scale 288.5 stands about 1,150 tall on a 199-high collision box)."""
    sys.path.insert(0, str(ROOT / "tools"))
    from item_model_shapes import gltf_bounds
    import yaml
    bindings = yaml.load((WORLD / "models/actors.yml").read_text(), Loader=yaml.CSafeLoader)["actors"]
    by_descriptor = {b["descriptor"]: b for b in bindings}
    bounds: dict[str, tuple[float, float, float]] = {}
    sizes: dict[int, tuple[float, float, float, str]] = {}
    for line in (WORLD / "data_tables/monster_data.txt").read_text().splitlines():
        row = line.split("\t")
        if not row[0].isdigit() or len(row) < 3 or row[2] not in by_descriptor:
            continue
        binding = by_descriptor[row[2]]
        key = f"{binding['model']}@{binding.get('scale', 1.0)}"
        if key not in bounds:
            try:
                low, high = gltf_bounds(ROOT / "assets_dev" / binding["model"])
            except (OSError, ValueError):
                continue
            extent = (high - low) * float(binding.get("scale", 1.0))
            bounds[key] = (max(extent[0], extent[2]) / 2, float(extent[1]), max(extent[0], extent[2]))
        sizes[int(row[0])] = (*bounds[key], Path(binding["model"]).name)
    return sizes


def monster_sizes() -> dict[int, tuple[float, float]]:
    """Each monster's collision radius and height, from its placed actors, else from its descriptor row."""
    sizes: dict[int, tuple[float, float]] = {}
    descriptors: dict[str, tuple[float, float]] = {}
    for line in (WORLD / "data_tables/monster_descriptors.txt").read_text().splitlines():
        row = line.split("\t")
        if row[0].isdigit() and len(row) > 3:
            descriptors[row[1]] = (float(row[3]), float(row[2]))
    for line in (WORLD / "data_tables/monster_data.txt").read_text().splitlines():
        row = line.split("\t")
        if row[0].isdigit() and len(row) > 2 and row[2] in descriptors:
            sizes[int(row[0])] = descriptors[row[2]]
    placed: set[int] = set()
    for path in (WORLD / "maps").glob("*.scene.yml"):
        text = path.read_text()
        scene = json.loads(text) if text.lstrip().startswith("{") else None
        if scene is None:
            import yaml
            scene = yaml.load(text, Loader=yaml.CSafeLoader)
        for actor in scene["initial_state"]["actors"]:
            monster = actor.get("monster_info_id")
            if monster and monster not in placed:
                placed.add(monster)
                sizes[monster] = (float(actor.get("radius", 40)), float(actor.get("height", 150)))
    return sizes


def capture(monster_id: int, size: tuple[float, float, float], closer: float) -> tuple[int, bool]:
    radius, height, depth = size
    # The distance to the monster's front (a rat or a dragon facing the camera reaches half its length closer).
    distance = (max(170.0, height * 1.5, radius * 2.4, (EYE - height * 0.5) * 2.0) + depth * 0.35) * closer
    cx, cy, z = CENTRE
    # The monster's back clear of the hall's north wall, the party clear of the south wall.
    monster_y = min(cy + distance / 2, HALL_Y[1] - depth / 2 - 100.0)
    party_y = max(monster_y - distance, HALL_Y[0] + 64.0)
    distance = monster_y - party_y
    pitch = math.atan2(height * 0.5 - EYE, distance) - CROP_AIM
    work = WORK / str(monster_id)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    (work / "arena.yml").write_text(
        f"name: xeenguide_{monster_id}\nworld: xeen\nmap: {MAP}\n"
        f"party:\n  position: [{cx}, {party_y:.0f}, {z}]\n  yaw_degrees: 90\n  invulnerable: true\n"
        f"monsters:\n  - monster_id: {monster_id}\n    position: [{cx}, {monster_y:.0f}, {z}]\n"
        f"    yaw_degrees: 270\n    hostile: false\n")
    (work / "tour.yml").write_text(
        f"output_dir: {work}\nsettle_seconds: 3\nexit: true\nshots:\n"
        f"  - name: portrait\n    position: [{cx}, {party_y:.0f}, {z}]\n    yaw: {math.pi / 2:.4f}\n"
        f"    pitch: {pitch:.4f}\n    time: \"12:00\"\n")
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    env.setdefault("OPENYAMM_GAME_BINARY", str(ROOT / "build-xeen/game/openyamm"))
    command = [str(ROOT / "tools/run_game.sh"), "--isolated", f"xeenmonster_{monster_id}", "--world", "xeen", "--map", MAP,
               "--warmup", "2", "--seconds", "90",
               "--set", f"debug.ai_arena_path={work / 'arena.yml'}",
               "--set", f"debug.screenshot_tour_path={work / 'tour.yml'}"]
    subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)
    shots = sorted(work.glob("*.png"))
    if not shots:
        return monster_id, False
    image = Image.open(shots[0]).convert("RGB")
    mm9.remove_crosshair(image)
    w, h = image.size
    image.crop((int(w * CROP[0]), int(h * CROP[1]), int(w * CROP[2]), int(h * CROP[3]))).save(OUT / f"{monster_id}.png")
    return monster_id, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ids", help="comma-separated monster ids (default: every bestiary monster)")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--missing", action="store_true", help="only monsters without a portrait yet")
    args = parser.parse_args()
    guide_js = (ROOT / "output/xeen_site/data/guide.js").read_text()
    guide = json.loads(guide_js[guide_js.index("{"):guide_js.rindex("}") + 1])
    ids = [int(i) for i in args.ids.split(",")] if args.ids else [m["id"] for m in guide["monsters"]]
    if args.missing:
        ids = [i for i in ids if not (OUT / f"{i}.png").exists()]
    placed = monster_sizes()
    drawn = model_sizes()
    sizes = {}
    for monster_id in ids:
        radius, height = placed.get(monster_id, (40.0, 150.0))
        model = drawn.get(monster_id, (0.0, 0.0, 0.0, ""))
        sizes[monster_id] = (max(radius, model[0]), max(height, model[1]), max(radius * 2, model[2]),
                             CLOSER.get(model[3], 1.0))
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=min(args.jobs, 2)) as pool:
        for monster_id, ok in pool.map(lambda i: capture(i, sizes[i][:3], sizes[i][3]), ids):
            print(f"{monster_id}: {'ok' if ok else 'no capture'}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
