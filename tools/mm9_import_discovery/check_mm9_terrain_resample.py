#!/usr/bin/env python3
"""
Measure how much of an MM9 exterior's terrain survives resampling to the classic 128x128 ODM height grid.

Rasterizes every DAT polygon textured from a `terrain` texture folder (the MM9 terrain world models), samples the
top surface at the 512-unit ODM nodes (32-unit height steps), interpolates it back over the classic two-triangle
cells and compares it with a 64-unit raster of the original. Writes images and a short report; changes no game data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion

from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE
from transcode_mm9_dat_to_odm import read_dat_world

HALF_EXTENT = 32768
CELL = 512
HEIGHT_STEP = 32
FINE_STEP = 64
SHORE_BAND = 768
# Water volumes, the hidden visibility helper and the collision hull (which closes the world with a lid at the sky
# ceiling and blocking boxes) also carry terrain textures; none of them is the visible walkable terrain.
WATER_MODEL_PREFIXES = ("bluewater", "clearwater", "ocean", "water")
HELPER_MODELS = {"visbsp", "physicsbsp"}


def terrain_triangles(dat_path: Path) -> tuple[np.ndarray, float | None]:
    world = read_dat_world(dat_path)
    triangles = []
    sea_level = None
    for model in world.world_models:
        name = model.name.lower()
        if name.startswith(WATER_MODEL_PREFIXES):
            sea_level = model.max_box[1] if sea_level is None else min(sea_level, model.max_box[1])
            continue
        if name in HELPER_MODELS:
            continue
        for poly in model.polies:
            texture = model.textures[model.surfaces[poly.surface_index].texture_index].lower()
            if "\\terrain\\" not in texture:
                continue
            points = [model.points[vertex.vertex_index] for vertex in poly.disk_verts]
            for index in range(1, len(points) - 1):
                triangles.append((points[0], points[index], points[index + 1]))
    return np.array(triangles, dtype=np.float64), sea_level


def to_openyamm(triangles: np.ndarray, sea_level: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # LithTech is Y-up; heights are measured from sea level so the sea sits at ODM height 0.
    x = triangles[:, :, 0] * SCALE
    y = triangles[:, :, 2] * SCALE
    z = (triangles[:, :, 1] - sea_level) * SCALE
    x -= (x.min() + x.max()) / 2
    y -= (y.min() + y.max()) / 2
    return x, y, z


def rasterize(x: np.ndarray, y: np.ndarray, z: np.ndarray, step: int):
    size = int(2 * HALF_EXTENT / step) + 1
    top = np.full((size, size), -1e9)
    low = np.full((size, size), 1e9)
    count = np.zeros((size, size), np.int16)
    for tx, ty, tz in zip(x, y, z):
        denominator = (ty[1] - ty[2]) * (tx[0] - tx[2]) + (tx[2] - tx[1]) * (ty[0] - ty[2])
        if abs(denominator) < 1e-6:
            continue
        columns = np.arange(max(int(np.floor((tx.min() + HALF_EXTENT) / step)), 0),
                            min(int(np.ceil((tx.max() + HALF_EXTENT) / step)), size - 1) + 1)
        rows = np.arange(max(int(np.floor((ty.min() + HALF_EXTENT) / step)), 0),
                         min(int(np.ceil((ty.max() + HALF_EXTENT) / step)), size - 1) + 1)
        if len(columns) == 0 or len(rows) == 0:
            continue
        gx, gy = np.meshgrid(columns * step - HALF_EXTENT, rows * step - HALF_EXTENT, indexing="xy")
        a = ((ty[1] - ty[2]) * (gx - tx[2]) + (tx[2] - tx[1]) * (gy - ty[2])) / denominator
        b = ((ty[2] - ty[0]) * (gx - tx[2]) + (tx[0] - tx[2]) * (gy - ty[2])) / denominator
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if not inside.any():
            continue
        height = a * tz[0] + b * tz[1] + c * tz[2]
        window = (slice(rows[0], rows[-1] + 1), slice(columns[0], columns[-1] + 1))
        top_window, low_window, count_window = top[window], low[window], count[window]
        top_window[inside] = np.maximum(top_window[inside], height[inside])
        low_window[inside] = np.minimum(low_window[inside], height[inside])
        count_window[inside] += 1
    return top, low, count


def interpolate_cells(heights: np.ndarray, size: int) -> np.ndarray:
    coordinates = np.arange(size) * FINE_STEP / CELL
    cell = np.floor(coordinates).astype(int).clip(0, heights.shape[0] - 2)
    fraction = coordinates - cell
    ci, cj = np.meshgrid(cell, cell, indexing="xy")
    fx, fy = np.meshgrid(fraction, fraction, indexing="xy")
    h00, h10 = heights[cj, ci], heights[cj, ci + 1]
    h01, h11 = heights[cj + 1, ci], heights[cj + 1, ci + 1]
    lower = fx + fy <= 1
    return np.where(lower, h00 + (h10 - h00) * fx + (h01 - h00) * fy,
                    h11 + (h01 - h11) * (1 - fx) + (h10 - h11) * (1 - fy))


def save_comparison(path: Path, fine: np.ndarray, resampled: np.ndarray, error: np.ndarray, land: np.ndarray,
                    stacked: np.ndarray) -> None:
    sea = np.array([20, 40, 90], np.uint8)
    top = max(fine.max(), 1.0)

    def grey(values: np.ndarray) -> np.ndarray:
        level = (np.clip(values / top, 0, 1) * 255).astype(np.uint8)
        image = np.stack([level] * 3, -1)
        image[~land] = sea
        return image

    level = (np.clip(error / 256, 0, 1) * 255).astype(np.uint8)
    error_image = np.stack([level, (255 - level) * land, np.zeros_like(level)], -1).astype(np.uint8)
    error_image[~land] = sea
    error_image[stacked] = [255, 0, 255]
    panels = [grey(fine), grey(resampled), error_image]
    rows, columns = np.where(land)
    crop = (slice(max(rows.min() - 8, 0), rows.max() + 8), slice(max(columns.min() - 8, 0), columns.max() + 8))
    gap = np.full((panels[0][crop].shape[0], 8, 3), 255, np.uint8)
    strip = np.concatenate([np.concatenate([panel[crop][::-1], gap], 1) for panel in panels], 1)
    Image.fromarray(strip).save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat", type=Path, help="MM9 WORLDS/*.dat")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--sea-level", type=float, help="Sea level in LithTech units (default: the lowest water surface)")
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    triangles, water_level = terrain_triangles(arguments.dat)
    sea_level = arguments.sea_level if arguments.sea_level is not None else water_level
    if sea_level is None:
        sea_level = float(triangles[:, :, 1].min())
    x, y, z = to_openyamm(triangles, sea_level)
    print(f"terrain triangles {len(x)}, sea level LT {sea_level:.0f}, extent {x.max() - x.min():.0f} x "
          f"{y.max() - y.min():.0f}, height up to {z.max():.0f}")

    nodes, _, _ = rasterize(x, y, z, CELL)
    heights = np.round(np.where(nodes < -1e8, 0, np.clip(nodes, 0, 255 * HEIGHT_STEP)) / HEIGHT_STEP) * HEIGHT_STEP
    top, low, count = rasterize(x, y, z, FINE_STEP)
    covered = top > -1e8
    fine = np.where(covered, np.maximum(top, 0), 0)
    resampled = interpolate_cells(heights, fine.shape[0])
    error = np.abs(resampled - fine)
    land = covered & (fine > 16)
    inland = binary_erosion(land, iterations=SHORE_BAND // FINE_STEP)
    stacked = (count >= 2) & ((top - low) > 200)
    gradient_y, gradient_x = np.gradient(fine, FINE_STEP)
    slope = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))

    for label, mask in (("all land", land), ("inland", inland), (f"shore band {SHORE_BAND}", land & ~inland),
                        ("inland, slope < 30", inland & (slope < 30)), ("inland, slope > 45", inland & (slope > 45))):
        values = error[mask]
        if values.size:
            print(f"{label}: mean error {values.mean():.0f}, p95 {np.percentile(values, 95):.0f}, "
                  f">128 {100 * (values > 128).mean():.1f} %, >256 {100 * (values > 256).mean():.1f} %")
    print(f"inland slope > 45 deg at {FINE_STEP}-unit scale: {100 * (slope[inland] > 45).mean():.1f} %")
    print(f"stacked surfaces (overhangs, arches, >200 apart): {100 * stacked.sum() / max(land.sum(), 1):.2f} % of land")
    print(f"highest height byte {int(heights.max() / HEIGHT_STEP)}")

    np.save(arguments.output_dir / "heights_129.npy", heights)
    save_comparison(arguments.output_dir / "comparison.png", fine, np.where(land, resampled, 0), error, land, stacked)
    print(f"wrote {arguments.output_dir / 'comparison.png'} (original | resampled | error: green 0, red >= 256, "
          "magenta stacked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
