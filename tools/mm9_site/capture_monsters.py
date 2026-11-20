#!/usr/bin/env python3
"""Portraits for the MM9 guide's bestiary: each monster alone in The Arena's pit (an AI arena that clears the map's
actors and spawns only it, not hostile), photographed from the front by a one-shot screenshot tour, the HUD cropped
away. One isolated game boot per monster (tools/RUN_GAME.md, tests/scenarios/mm9/ai/README.md).

Run after build_site.py (reads output/mm9_site/data/guide.js for the monsters); writes output/mm9_site_monsters/
<id>.png. build_site.py then packs them into img/monsters.webp.

    python3 tools/mm9_site/capture_monsters.py [--ids 9101,9114] [--jobs 3]
"""

from __future__ import annotations

import argparse
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
WORLD = ROOT / "assets_dev/worlds/mm9"
OUT = ROOT / "output/mm9_site_monsters"
WORK = OUT / "work"

PARTY = (0.0, -1100.0, 1.0)   # The Arena's pit floor is at z = 1, open within about 1 380 of the centre
EYE = 152.0                    # worlds/mm9/world.yml partyMovement.eyeHeight
CROP = (0.2, 0.07, 0.8, 0.77)  # the frame without the HUD: top bar, portraits, minimap, party basebar
CROP_AIM = 0.09                # radians up, so the monster sits in the middle of the crop (0.42 of the frame height)


def monster_sizes() -> dict[int, tuple[float, float]]:
    """Each monster's collision radius and height, from its placed actors."""
    sizes: dict[int, tuple[float, float]] = {}
    for path in (WORLD / "maps").glob("*.scene.yml"):
        for actor in json.loads(path.read_text())["initial_state"]["actors"]:
            monster = actor.get("monster_id")
            if monster and monster not in sizes:
                sizes[monster] = (float(actor.get("radius", 40)), float(actor.get("height", 150)))
    return sizes


def remove_crosshair(image: Image.Image) -> None:
    """Paint out the gameplay crosshair at the frame centre (2-pixel arms with a 1-pixel shadow, a 4-pixel gap):
    each arm pixel becomes the blend of the pixels just outside the arm."""
    pixels = image.load()
    cx, cy = image.width // 2, image.height // 2

    def blend(a, b, t):
        return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

    for y in range(cy - 9, cy + 9):          # the vertical arms: columns cx-2 .. cx+1
        left, right = pixels[cx - 3, y], pixels[cx + 2, y]
        for k, x in enumerate(range(cx - 2, cx + 2)):
            pixels[x, y] = blend(left, right, (k + 1) / 5)
    for x in range(cx - 9, cx + 9):          # the horizontal arms: rows cy-2 .. cy+1
        top, bottom = pixels[x, cy - 3], pixels[x, cy + 2]
        for k, y in enumerate(range(cy - 2, cy + 2)):
            pixels[x, y] = blend(top, bottom, (k + 1) / 5)


def capture(monster_id: int, size: tuple[float, float]) -> tuple[int, bool]:
    radius, height = size
    distance = max(170.0, height * 2.0, radius * 3.2, (EYE - height * 0.5) * 2.4)
    # Small and middling monsters stand in front of the party's usual spot; giants stand in the pit's centre, with
    # the camera as far back as the pit allows.
    monster_y = PARTY[1] + distance if distance <= 1200 else 600.0
    party_y = max(monster_y - distance, -1300.0)
    distance = monster_y - party_y
    pitch = math.atan2(height * 0.5 - EYE, distance) + CROP_AIM
    work = WORK / str(monster_id)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    x, _, z = PARTY
    y = party_y
    (work / "arena.yml").write_text(
        f"name: guide_{monster_id}\nworld: mm9\nmap: thearena.blv\n"
        f"party:\n  position: [{x}, {y}, {z}]\n  yaw_degrees: 90\n  invulnerable: true\n"
        f"monsters:\n  - monster_id: {monster_id}\n    position: [{x}, {monster_y:.0f}, {z}]\n"
        f"    yaw_degrees: 270\n    hostile: false\n")
    (work / "tour.yml").write_text(
        f"output_dir: {work}\nsettle_seconds: 3\nexit: true\nshots:\n"
        f"  - name: portrait\n    position: [{x}, {y}, {z}]\n    yaw: {math.pi / 2:.4f}\n    pitch: {pitch:.4f}\n"
        f'    time: "12:00"\n')
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    command = [str(ROOT / "tools/run_game.sh"), "--isolated", f"mm9monster_{monster_id}", "--world", "mm9", "--map",
               "thearena.blv", "--warmup", "2", "--seconds", "90",
               "--set", f"debug.ai_arena_path={work / 'arena.yml'}",
               "--set", f"debug.screenshot_tour_path={work / 'tour.yml'}"]
    subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)
    shots = sorted(work.glob("*.png"))
    if not shots:
        return monster_id, False
    image = Image.open(shots[0]).convert("RGB")
    remove_crosshair(image)
    w, h = image.size
    image.crop((int(w * CROP[0]), int(h * CROP[1]), int(w * CROP[2]), int(h * CROP[3]))).save(OUT / f"{monster_id}.png")
    return monster_id, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ids", help="comma-separated monster ids (default: every bestiary monster)")
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    guide_js = (ROOT / "output/mm9_site/data/guide.js").read_text()
    guide = json.loads(guide_js[guide_js.index("{"):guide_js.rindex("}") + 1])
    ids = [int(i) for i in args.ids.split(",")] if args.ids else [m["id"] for m in guide["monsters"]]
    sizes = monster_sizes()
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for monster_id, ok in pool.map(lambda i: capture(i, sizes.get(i, (40.0, 150.0))), ids):
            print(f"{monster_id}: {'ok' if ok else 'no capture'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
