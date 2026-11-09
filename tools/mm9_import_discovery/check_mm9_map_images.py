#!/usr/bin/env python3
"""Checks that MM9's painted maps fit the rebuilt maps: every map in worlds/mm9/ui/maps/catalog.yml is loaded by the
game (`--headless-export-indoor-bake-scene`), its walkable floors are projected through the catalog entry (bounds,
flips) onto the floor image its height selects (the variants' minimum_z < z <= maximum_z, as the game picks it), and
the outline of those floors is matched against the lines drawn on the image.

    python3 -B tools/mm9_import_discovery/check_mm9_map_images.py                    # every map, assets_dev
    python3 -B tools/mm9_import_discovery/check_mm9_map_images.py lichlab bathhouse  # some maps
    python3 -B tools/mm9_import_discovery/check_mm9_map_images.py --assets output/mm9_rework/assets_dev

Per image it projects two sets of points: the outline of the floors (dungeons draw their rooms) and the feet of the
walls (cities and regions draw buildings), and measures the mean distance from them to the nearest drawn line (capped
at 3 px, so features the painter left out add a constant). The set closer to the ink decides. It then searches shifts of
up to 16 native px and scales of 0.95-1.05 for the best match. FAIL: the best match is better than the catalog's own
placement by over 1 px (the entry is wrong). check: a better match moves the points by over 2 px on average and gains
over 0.3 px (look at the overlay). The painted regions have little ink: a wrong entry there may only show as check,
so their overlays are the check. For a map with several floor images, each band must match its own image best (a
wrong height threshold shows as a band matching another floor's image).

Writes <out>/report.json and <out>/<map>_<variant>.png overlays (floors tinted by band, wall feet magenta).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[2]
CAP = 3.0
SHIFT = 16
# Calibrated on 2026-11-09 by moving every entry 8 px and stretching it 3 %: the moved entries improved by 1.1-2.0 px
# at their best match (dungeons and cities with inked walls; the painted regions only by about 0.5), the installed
# entries by at most 0.62 (Kluso's House, about 2 px = 50 units off on both floors in the original too).
FAIL_GAIN = 1.0
CHECK_GAIN = 0.3
ORIGINAL_CATALOG = ROOT / "level_generation/projects/mm9r_common/original_tables/catalog.yml"
TINTS = [(230, 40, 40), (30, 140, 255), (20, 190, 60), (200, 60, 220)]


def load_image(assets: Path, texture: str, width: int, height: int) -> np.ndarray:
    """The variant's image at its native size (the catalog's width and height), as the game resolves the name."""
    stem = (assets / "worlds/mm9" / texture).with_suffix("")
    path = next((stem.with_suffix(s) for s in (".png", ".bmp", ".pcx") if stem.with_suffix(s).exists()), None)
    if path is None:
        raise FileNotFoundError(f"no image for {texture}")
    image = Image.open(path).convert("RGB")
    if image.size != (width, height):
        image = image.resize((width, height), Image.LANCZOS)
    return np.asarray(image)


def drawn_lines(image: np.ndarray) -> np.ndarray:
    """The dark ink of the map: pixels well below the local parchment brightness."""
    lum = image.astype(np.float32).mean(axis=2)
    background = gaussian_filter(lum, 6.0)
    return (background - lum) > 35.0


def variant_index(variants: list, z: float) -> int:
    for index, variant in enumerate(variants):
        low, high = variant.get("minimum_z"), variant.get("maximum_z")
        if (low is None or z > low) and (high is None or z <= high):
            return index
    return 0


def project(entry: dict, points: np.ndarray, width: int, height: int) -> np.ndarray:
    bounds = entry["world_bounds"]
    u = (points[:, 0] - bounds["min_x"]) / (bounds["max_x"] - bounds["min_x"])
    v = (points[:, 1] - bounds["min_y"]) / (bounds["max_y"] - bounds["min_y"])
    if entry.get("flip_u", False):
        u = 1.0 - u
    if entry.get("flip_v", True):
        v = 1.0 - v
    return np.stack([u * width, v * height], axis=1)


def floor_mask(entry: dict, floors: list, width: int, height: int) -> np.ndarray:
    canvas = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(canvas)
    for _, points, _ in floors:
        draw.polygon([tuple(p) for p in project(entry, points, width, height)], fill=255)
    return np.asarray(canvas) > 0


def outline(mask: np.ndarray) -> np.ndarray:
    """Pixel coordinates (x, y) of the floor mask's boundary."""
    edge = mask & ~binary_erosion(mask, iterations=1, border_value=0)
    ys, xs = np.nonzero(edge)
    return np.stack([xs, ys], axis=1).astype(np.float32)


def score(distance: np.ndarray, points: np.ndarray, dx: float, dy: float, sx: float, sy: float) -> float:
    height, width = distance.shape
    cx, cy = width / 2.0, height / 2.0
    x = np.rint((points[:, 0] - cx) * sx + cx + dx).astype(np.int64)
    y = np.rint((points[:, 1] - cy) * sy + cy + dy).astype(np.int64)
    inside = (x >= 0) & (x < width) & (y >= 0) & (y < height)
    values = np.full(len(points), CAP, dtype=np.float32)
    values[inside] = np.minimum(distance[y[inside], x[inside]], CAP)
    return float(values.mean())


def best_fit(distance: np.ndarray, points: np.ndarray) -> dict:
    trials = {}
    for dy in range(-SHIFT, SHIFT + 1):
        for dx in range(-SHIFT, SHIFT + 1):
            trials[(dx, dy, 1.0, 1.0)] = score(distance, points, dx, dy, 1.0, 1.0)
    dx0, dy0, _, _ = min(trials, key=trials.get)
    for sx in np.arange(0.95, 1.0501, 0.01):
        for sy in np.arange(0.95, 1.0501, 0.01):
            for dy in range(dy0 - 3, dy0 + 4):
                for dx in range(dx0 - 3, dx0 + 4):
                    key = (dx, dy, round(float(sx), 2), round(float(sy), 2))
                    if key not in trials:
                        trials[key] = score(distance, points, *key)
    best = min(trials, key=trials.get)
    height, width = distance.shape
    moved = np.stack([(points[:, 0] - width / 2.0) * (best[2] - 1.0) + best[0],
                      (points[:, 1] - height / 2.0) * (best[3] - 1.0) + best[1]], axis=1)
    return {"shift": [best[0], best[1]], "scale": [best[2], best[3]], "best": round(trials[best], 3),
            "identity": round(trials[(0, 0, 1.0, 1.0)], 3),
            "displacement": round(float(np.linalg.norm(moved, axis=1).mean()), 2)}


def refine(entry: dict, measured: list) -> tuple[dict, dict]:
    """One shift and scale for the whole map (every floor image together: they share the bounds), in the first image's
    pixels, searched coarse to fine; returns the fit and the entry's bounds moved by it."""
    width0 = entry["variants"][0]["width"]
    height0 = entry["variants"][0]["height"]
    total = sum(len(points) for _, points in measured)

    def joint(dx: float, dy: float, sx: float, sy: float) -> float:
        value = 0.0
        for distance, points in measured:
            height, width = distance.shape
            value += score(distance, points, dx * width / width0, dy * height / height0, sx, sy) * len(points)
        return value / total

    trials = {}

    def search(dxs, dys, sxs, sys_):
        for sx in sxs:
            for sy in sys_:
                for dy in dys:
                    for dx in dxs:
                        key = (round(float(dx), 3), round(float(dy), 3), round(float(sx), 4), round(float(sy), 4))
                        if key not in trials:
                            trials[key] = joint(*key)
        return min(trials, key=trials.get)

    best = search(range(-SHIFT, SHIFT + 1), range(-SHIFT, SHIFT + 1), [1.0], [1.0])
    best = search(np.arange(best[0] - 3, best[0] + 3.01), np.arange(best[1] - 3, best[1] + 3.01),
                  np.arange(0.95, 1.0501, 0.01), np.arange(0.95, 1.0501, 0.01))
    best = search(np.arange(best[0] - 1, best[0] + 1.01, 0.25), np.arange(best[1] - 1, best[1] + 1.01, 0.25),
                  np.arange(best[2] - 0.01, best[2] + 0.0101, 0.0025), np.arange(best[3] - 0.01, best[3] + 0.0101, 0.0025))
    dx, dy, sx, sy = best
    bounds = dict(entry["world_bounds"])
    for low, high, shift, scale, size, flipped in (("min_x", "max_x", dx, sx, width0, entry.get("flip_u", False)),
                                                   ("min_y", "max_y", dy, sy, height0, entry.get("flip_v", True))):
        extent = bounds[high] - bounds[low]
        k = 0.5 - 0.5 * scale + (-shift if flipped else shift) / size
        bounds[low] = round(bounds[low] - k * extent / scale, 2)
        bounds[high] = round(bounds[low] + extent / scale, 2)
    fit = {"shift": [dx, dy], "scale": [sx, sy], "identity": round(joint(0, 0, 1.0, 1.0), 3),
           "best": round(trials[best], 3)}
    return fit, bounds


def export_floors(game: Path, assets: Path, map_file: str, work: Path) -> tuple[list, list]:
    out = work / f"{Path(map_file).stem}.json"
    subprocess.run([str(game), "--asset-root", str(assets), "--world", "mm9", "--headless-export-indoor-bake-scene",
                    map_file, str(out)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    scene = json.loads(out.read_text())
    floors, walls = [], []
    for face in scene["faces"]:
        if not face["visible"]:
            continue
        points = np.asarray(face["points"], dtype=np.float64)
        normal_z = face["plane_normal"][2] / 65536.0
        if normal_z >= 0.7:
            floors.append((float(points[:, 2].mean()), points[:, :2], normal_z))
        elif abs(normal_z) < 0.3 and points[:, 2].max() - points[:, 2].min() >= 64:
            # A wall's foot: its points within 8 units of its lowest, seen from above as a segment.
            low = points[points[:, 2] <= points[:, 2].min() + 8]
            if len(low) >= 2:
                span = low[:, :2]
                ends = span[np.argsort(span @ (span[-1] - span[0]))[[0, -1]]]
                walls.append((float(points[:, 2].min()), ends))
    return floors, walls


def wall_points(entry: dict, walls: list, width: int, height: int) -> np.ndarray:
    """Pixel samples along the walls' feet, one per pixel of length."""
    samples = []
    for _, ends in walls:
        a, b = project(entry, ends, width, height)
        count = max(2, int(np.ceil(np.linalg.norm(b - a))) + 1)
        samples.append(a + (b - a) * np.linspace(0.0, 1.0, count)[:, None])
    if not samples:
        return np.zeros((0, 2), dtype=np.float32)
    points = np.rint(np.concatenate(samples)).astype(np.int64)
    inside = (points[:, 0] >= 0) & (points[:, 0] < width) & (points[:, 1] >= 0) & (points[:, 1] < height)
    return np.unique(points[inside], axis=0).astype(np.float32)


def near_share(distance: np.ndarray, points: np.ndarray) -> float:
    return float((distance[points[:, 1].astype(int), points[:, 0].astype(int)] <= 3.0).mean())


def check_map(entry: dict, floors: list, walls: list, assets: Path, out: Path) -> dict:
    variants = entry["variants"]
    floor_bands = [[] for _ in variants]
    wall_bands = [[] for _ in variants]
    for floor in floors:
        floor_bands[variant_index(variants, floor[0])].append(floor)
    for wall in walls:
        wall_bands[variant_index(variants, wall[0])].append(wall)
    images, distances = [], []
    for variant in variants:
        image = load_image(assets, variant["texture"], variant["width"], variant["height"])
        images.append(image)
        distances.append(distance_transform_edt(~drawn_lines(image)))

    result = {"map": entry["map"], "variants": [], "ok": True}
    measured = []
    for index, variant in enumerate(variants):
        width, height = variant["width"], variant["height"]
        mask = floor_mask(entry, floor_bands[index], width, height)
        # Two measures: the floors' outline (dungeons draw their rooms) and the walls' feet (cities draw buildings).
        # The one closer to the ink at the catalog's placement decides.
        candidates = {"floors": outline(mask), "walls": wall_points(entry, wall_bands[index], width, height)}
        candidates = {name: points for name, points in candidates.items() if len(points) >= 50}
        record = {"texture": variant["texture"], "floors": len(floor_bands[index]), "walls": len(wall_bands[index])}
        if not candidates:
            record["status"] = "no floors"
            result["variants"].append(record)
            measured.append(None)
            continue
        name = max(candidates, key=lambda key: near_share(distances[index], candidates[key]))
        points = candidates[name]
        measured.append(points)
        fit = best_fit(distances[index], points)
        record.update(fit)
        record["measure"] = name
        record["near_line"] = round(near_share(distances[index], points), 3)
        gain = fit["identity"] - fit["best"]
        bad = gain > FAIL_GAIN
        record["status"] = "FAIL" if bad else "check" if fit["displacement"] > 2.0 and gain > CHECK_GAIN else "ok"
        result["ok"] &= not bad
        result["variants"].append(record)

        tint = np.zeros_like(images[index])
        tint[mask] = TINTS[index % len(TINTS)]
        alpha = (mask * 0.45)[..., None]
        overlay = (images[index] * (1 - alpha) + tint * alpha).astype(np.uint8)
        wall = wall_points(entry, wall_bands[index], width, height).astype(int)
        overlay[wall[:, 1], wall[:, 0]] = (255, 0, 255)
        Image.fromarray(overlay).save(out / f"{entry['map']}_{index}.png")

    # Bands against images: each band's floors should match its own image best.
    if len(variants) > 1:
        matrix = []
        for band, points in enumerate(measured):
            row = [None if points is None else round(score(distances[image], points, 0, 0, 1.0, 1.0), 3)
                   for image in range(len(variants))]
            matrix.append(row)
            own = row[band]
            if own is not None and any(v is not None and v < own - 0.25 for i, v in enumerate(row) if i != band):
                result["ok"] = False
                result.setdefault("band_errors", []).append(band)
        result["band_matrix"] = matrix
    result["measured"] = [(distances[i], points) for i, points in enumerate(measured) if points is not None]
    return result


def write_refinements(path: Path, refinements: dict, entries: list) -> None:
    """Merges the moved bounds into the refinement table, in the old import's frame (the converters move the entry by
    the project's offset afterwards): the table's frame differs from the catalog's by the original entry's offset."""
    original = {e["map"]: e for e in yaml.safe_load(ORIGINAL_CATALOG.read_text())["maps"]}
    table = yaml.safe_load(path.read_text()) if path.exists() else None
    table = table or {"format_version": 1, "maps": {}}
    for entry in entries:
        if entry["map"] not in refinements:
            continue
        fit, bounds = refinements[entry["map"]]
        source = original[entry["map"]]["world_bounds"]
        moved = {}
        for key in ("min_x", "max_x", "min_y", "max_y"):
            axis_key = "min_x" if key.endswith("_x") else "min_y"
            moved[key] = round(bounds[key] + source[axis_key] - entry["world_bounds"][axis_key], 2)
        table["maps"][entry["map"]] = {"world_bounds": moved, "fit": fit}
    header = ("# MM9's painted maps whose drawing does not match MM9's own bounds (the DAT header's extent): bounds\n"
              "# measured against the rebuilt floors and walls by tools/mm9_import_discovery/check_mm9_map_images.py\n"
              "# --refine, in the old import's frame. dungeon/tables.py catalog_text uses them in place of catalog.yml's.\n"
              "# fit: the shift (first image's px) and scale that moved the bounds; identity/best: mean distance to\n"
              "# the ink before and after (px).\n")
    path.write_text(header + yaml.safe_dump(table, sort_keys=True, default_flow_style=None))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("maps", nargs="*")
    parser.add_argument("--assets", type=Path, default=ROOT / "assets_dev")
    parser.add_argument("--catalog", type=Path, help="another catalog than the asset root's (a converter's draft)")
    parser.add_argument("--refine", type=Path, metavar="TABLE",
                        help="fit one shift and scale per named map and record the moved bounds (in the old import's "
                             "frame) in this table, e.g. level_generation/projects/mm9r_common/original_tables/"
                             "map_image_fit.yml; the converters' catalog step applies it")
    parser.add_argument("--game", type=Path, default=ROOT / "build/game/openyamm")
    parser.add_argument("--out", type=Path, default=ROOT / "output/mm9_map_image_fit")
    args = parser.parse_args()

    catalog = yaml.safe_load((args.catalog or args.assets / "worlds/mm9/ui/maps/catalog.yml").read_text())
    entries = [e for e in catalog["maps"] if not args.maps or e["map"] in args.maps]
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    refinements = {}
    with tempfile.TemporaryDirectory() as temporary:
        for entry in entries:
            floors, walls = export_floors(args.game, args.assets.resolve(), f"{entry['map']}.blv",
                                          Path(temporary))
            result = check_map(entry, floors, walls, args.assets, args.out)
            measured = result.pop("measured")
            results.append(result)
            if args.refine:
                if not args.maps:
                    parser.error("--refine needs the maps named")
                fit, bounds = refine(entry, measured)
                refinements[entry["map"]] = (fit, bounds)
                print(f"     {entry['map']}: refined {fit}")
            cells = []
            for v in result["variants"]:
                if "best" in v:
                    cells.append(f"{v['status']} {v['measure']} d {v['identity']:.2f}/{v['best']:.2f} "
                                 f"(best moves {v['displacement']:.1f}px: shift {v['shift']} scale {v['scale']}) "
                                 f"near {v['near_line']:.0%}")
                else:
                    cells.append(v["status"])
            extra = f" bands {result['band_matrix']}" if "band_matrix" in result else ""
            checks = any(v["status"] == "check" for v in result["variants"])
            flag = "FAIL" if not result["ok"] else "chk " if checks else "ok  "
            print(f"{flag} {entry['map']:22} " + " | ".join(cells) + extra)
    (args.out / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    if refinements:
        write_refinements(args.refine, refinements, entries)
    failed = [r["map"] for r in results if not r["ok"]]
    checks = [r["map"] for r in results if r["ok"] and any(v["status"] == "check" for v in r["variants"])]
    print(f"{len(results) - len(failed)} of {len(results)} maps fit"
          + (f"; look at the overlays of: {', '.join(checks)}" if checks else "")
          + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
