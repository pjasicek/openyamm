#!/usr/bin/env python3
"""
Measures an outdoor BLV region's grass against its ground and fits the short grass's tint so the mats match the
ground under them (level_generation/terrain/MEADOW.md: "capture one pose with video.terrain_decorations on and off,
and compare the changed pixels"; mats that do not match read as dashes, on MM9's grounds as rows of small bushes).

It picks grassy, gentle, dry poses from the region's terrain weights (terrain_blend.py's), captures each with the
grass on and off in the review root, takes the changed pixels' mean colour with the grass over the same pixels'
without, and writes the region's tint (its current tint over that ratio) into grass_tints.yml, which
terrain_blend.py's region_grass reads, so the mats stand to the ground as New Sorpigal's do (TARGET). Rerun terrain_blend.py for the region afterwards.

    python3 level_generation/projects/mm9r_common/grass_tint.py <project dir> [--root <review root>] [--out <dir>]
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "util"))
import terrain_blend  # noqa: E402
from map_export import parse_blv_file  # noqa: E402

TINTS = HERE / "grass_tints.yml"
GRID = 512                       # 128 units a cell
POSES = 3
CHANGED = 12                     # a pixel the grass changes by more than this in some channel is grass
# New Sorpigal's grass over its ground, measured the same way (oute3.odm at its start and two meadows, 2026-11-07,
# 783 675 pixels): its mats a little brighter than the ground under them. The regions are fitted to the same.
TARGET = np.array([1.061, 1.075, 1.057])
EYE = 180.0


def poses(root: Path, stem: str) -> list[tuple[float, float, float, float]]:
    """Up to POSES (x, y, ground z, yaw) on flat, dense grass above every water surface, spread over the region."""
    payload = parse_blv_file(root / f"worlds/mm9/maps/{stem}.blv")["payload"]
    scene = json.loads((root / f"worlds/mm9/maps/{stem}.scene.yml").read_text())
    textures = set(scene["terrain"]["textures"])
    faces = [face for face in payload["faces"] if (face.get("texture_name") or "").strip().lower() in textures
             and len(face["vertex_indices"]) >= 3 and not face.get("is_portal")]
    _, height = terrain_blend.rasterise(payload, [(face, 0) for face in faces], GRID, heights=True)
    config = yaml.safe_load((root / f"worlds/mm9/terrain_materials/{stem}_blv.yml").read_text())
    weights = np.asarray(Image.open(root / f"worlds/mm9/terrain_materials/{config['weights'][0]}"), float) / 255.0
    size = weights.shape[0]
    weights = weights.reshape(GRID, size // GRID, GRID, size // GRID, 4).mean(axis=(1, 3))
    density = sum(weights[..., index] * float(layer.get("meadow", 0.0))
                  for index, layer in enumerate(config["layers"][:config["weighted_layers"]]))
    water = max([piece["top"] for volume in scene.get("water_volumes") or [] for piece in volume["pieces"]],
                default=-1.0e9)
    finite = np.isfinite(height)
    units = 65536.0 / GRID
    gy, gx = np.gradient(np.where(finite, height, 0.0), units)
    good = (density > 0.75) & finite & (np.hypot(gx, gy) < 0.15) & (height > water + 64.0)
    good = ndimage.uniform_filter(good.astype(float), 15) > 0.97
    rows, columns = np.nonzero(good)
    result = []
    for index in np.linspace(0, len(rows) - 1, POSES).astype(int) if len(rows) else []:
        row, column = rows[index], columns[index]
        result.append((float((column + 0.5) * units - 32768.0), float(32768.0 - (row + 0.5) * units),
                       float(height[row, column]), float(index % 4) * 1.5708))
    return result


def capture(root: Path, stem: str, shots: list, grass: bool, out: Path) -> list[Path]:
    directory = out / ("on" if grass else "off")
    directory.mkdir(parents=True, exist_ok=True)
    tour = {"output_dir": str(directory), "settle_seconds": 2.0, "exit": True,
            "shots": [{"name": f"p{index}", "position": [x, y, z + 20.0], "yaw": yaw, "pitch": -0.45,
                       **({"settle_seconds": 5.0} if index == 0 else {})}
                      for index, (x, y, z, yaw) in enumerate(shots)]}
    tour_path = out / f"tour_{'on' if grass else 'off'}.yml"
    tour_path.write_text(yaml.safe_dump(tour))
    x, y, z, _ = shots[0]
    subprocess.run([str(ROOT / "tools/run_game.sh"), "--isolated", f"grasstint_{stem}", "--world", "mm9",
                    "--map", f"{stem}.blv", "--assets", str(root), "--position", str(x), str(y), str(z + 20.0),
                    "--yaw-radians", "0", "--pitch-degrees", "-10", "--warmup", "1", "--seconds", "90",
                    "--set", f"video.terrain_decorations={'true' if grass else 'false'}",
                    "--set", "video.weather_quality=off", "--set", f"debug.screenshot_tour_path={tour_path}"],
                   cwd=ROOT, env={**os.environ, "SDL_AUDIODRIVER": "dummy"}, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return [directory / f"{index + 1:02d}-p{index}.png" for index in range(len(shots))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT / "output/mm9_rework/isleofashes_blv_root")
    parser.add_argument("--out", type=Path, help="capture directory (default: a temporary one)")
    args = parser.parse_args()
    project = args.project.resolve()
    overrides = yaml.safe_load((project / "overrides.yml").read_text())
    stem = (overrides.get("map") or {}).get("stem") or project.name.removeprefix("mm9r_").removesuffix("_blv")
    root = args.root.resolve()
    region = yaml.safe_load((root / f"worlds/mm9/terrain_decorations/{stem}_blv.yml").read_text())
    tint = np.array(region["rules"][0]["tint"], float)
    shots = poses(root, stem)
    if not shots:
        print(f"{stem}: no grassy pose; tint left as it is")
        return 0
    out = args.out.resolve() if args.out else Path(tempfile.mkdtemp(prefix=f"grasstint_{stem}_"))
    on = capture(root, stem, shots, True, out)
    off = capture(root, stem, shots, False, out)
    grass_sum = np.zeros(3)
    ground_sum = np.zeros(3)
    count = 0
    for with_grass, without in zip(on, off):
        if not with_grass.exists() or not without.exists():
            continue
        a = np.asarray(Image.open(with_grass).convert("RGB"), float)
        b = np.asarray(Image.open(without).convert("RGB"), float)
        # The world between the HUD's top bar and the party's basebar.
        a, b = a[int(a.shape[0] * 0.2):int(a.shape[0] * 0.75)], b[int(b.shape[0] * 0.2):int(b.shape[0] * 0.75)]
        changed = np.abs(a - b).max(axis=2) > CHANGED
        grass_sum += a[changed].sum(axis=0)
        ground_sum += b[changed].sum(axis=0)
        count += int(changed.sum())
    if count < 1000:
        print(f"{stem}: too few grass pixels ({count}) in {out}; tint left as it is")
        return 1
    ratio = grass_sum / np.maximum(ground_sum, 1.0)
    fitted = np.clip(tint * TARGET / ratio, 0.05, 2.0)
    with open(TINTS.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        tints = yaml.safe_load(TINTS.read_text()) if TINTS.exists() else None
        tints = tints or {}
        tints[stem] = [round(float(v), 4) for v in fitted]
        header = ("# The short grass's tint per outdoor BLV region, fitted by grass_tint.py so the mats match the\n"
                  "# ground under them (read by terrain_blend.py region_grass).\n")
        TINTS.write_text(header + yaml.safe_dump(dict(sorted(tints.items())), default_flow_style=None))
    print(f"{stem}: {count} grass pixels, grass/ground {np.round(ratio, 3).tolist()}, "
          f"tint {np.round(tint, 3).tolist()} -> {tints[stem]} ({out})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
