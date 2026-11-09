#!/usr/bin/env python3
"""Top-down floor plans of the MM6-MM8 indoor maps for the MAW guide, drawn from the BLV geometry, and the positions of
their event faces and decorations for the guide's markers.

    python3 tools/maw_site/dungeon_plans.py --out <dir> [--only 6d01.blv ...] [--debug-events]

A plan is drawn like a parchment dungeon map: the walkable floors (floor and sloped faces) filled from dark (low) to
light (high), drawn from the lowest storey up so an upper floor covers what lies under it; the vertical walls of each
storey in ink after its floors; door faces in a heavier rust line; water and lava floors tinted. A soft burnt halo
around the floors sets them off the parchment. Portals, invisible faces, sky and ceilings are left out.

render_plan(map_file, out_png) returns {w, h, bounds: [min_x, min_y, max_x, max_y]}: world units, x to the right and
the image top at max_y, so u = (x - min_x) / (max_x - min_x) and v = (max_y - y) / (max_y - min_y).
indoor_event_points(map_file) returns event id -> [(x, y, z)]: the centres of the faces carrying the event and the
positions of the decorations that carry it.
"""

import argparse
import sys
import time
import zlib
from bisect import bisect_right
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from util.map_export import parse_blv_file  # noqa: E402

WORLDS = REPO / 'assets_dev' / 'worlds'
WORLD_IDS = ('mm6', 'mm7', 'mm8')

# Face attributes (game/FaceEnums.h) and facet types (1 wall, 3 floor, 4 sloped floor, 5 ceiling, 6 sloped ceiling).
PORTAL = 0x00000001
FLUID = 0x00000010
INVISIBLE = 0x00002000
INDOOR_SKY = 0x00400000
LAVA = 0x40000000
WALL = 1
FLOORS = (3, 4)

LONG_SIDE = 1600
SUPERSAMPLE = 2
MARGIN = 0.035

PARCHMENT = np.array([234, 219, 186], dtype=np.float32)
HALO = (150, 92, 34)
FLOOR_LOW = np.array([150, 92, 40], dtype=np.float32)
FLOOR_HIGH = np.array([238, 202, 132], dtype=np.float32)
WATER = np.array([112, 138, 140], dtype=np.float32)
LAVA_TINT = np.array([186, 70, 36], dtype=np.float32)
INK = (52, 34, 18)
DOOR_INK = (128, 48, 22)
STEP_INK = (104, 72, 40)

_PAYLOADS = {}


def find_map(map_file: str) -> Path | None:
    for world in WORLD_IDS:
        path = WORLDS / world / 'maps' / map_file.lower()
        if path.exists():
            return path
    return None


def load(map_file: str) -> dict | None:
    key = map_file.lower()
    if key not in _PAYLOADS:
        path = find_map(key)
        _PAYLOADS.clear()  # one map at a time keeps memory flat
        _PAYLOADS[key] = parse_blv_file(path)['payload'] if path else None
    return _PAYLOADS[key]


def face_points(payload: dict, face: dict) -> list[tuple[int, int, int]]:
    vertices = payload['vertices']
    result = []
    for index in face['vertex_indices']:
        if index < len(vertices):
            vertex = vertices[index]
            result.append((vertex['x'], vertex['y'], vertex['z']))
    return result


def drawn(face: dict) -> bool:
    return not (face['is_portal'] or face['attributes'] & (PORTAL | INVISIBLE | INDOOR_SKY))


def indoor_event_points(map_file: str) -> dict[int, list[tuple[float, float, float]]]:
    """Event id -> the centres of the faces and the decorations that carry it."""
    payload = load(map_file)
    result: dict[int, list[tuple[float, float, float]]] = {}
    if payload is None:
        return result
    for face in payload['faces']:
        event = (face['face_param'] or {}).get('cog_triggered') or 0
        points = face_points(payload, face)
        if event and points:
            centre = tuple(sum(p[i] for p in points) / len(points) for i in range(3))
            result.setdefault(event, []).append(centre)
    for entity in payload['entities']:
        position = entity['position']
        for key in ('event_id_primary', 'event_id_secondary'):
            event = entity.get(key) or 0
            if event:
                result.setdefault(event, []).append((position['x'], position['y'], position['z']))
    return result


def door_faces(payload: dict, map_path: Path) -> set[int]:
    """Faces of the map's doors (the scene's door records), drawn as doors when they are walls."""
    scene = map_path.with_suffix('.scene.yml')
    if not scene.exists():
        return set()
    faces = set()
    in_doors = False
    for line in scene.read_text().splitlines():
        if line.startswith('  doors:'):
            in_doors = True
        elif in_doors and line.startswith('  ') and not line.startswith('   ') and not line.startswith('  -'):
            break
        elif in_doors and line.strip().startswith('face_ids:'):
            text = line.split(':', 1)[1].strip().strip('[]')
            faces.update(int(x) for x in text.split(',') if x.strip())
    return faces


def parchment(width: int, height: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    coarse = Image.fromarray((rng.random((max(2, height // 96), max(2, width // 96))) * 255).astype(np.uint8))
    coarse = np.asarray(coarse.resize((width, height), Image.BICUBIC), dtype=np.float32) / 255.0
    fine = rng.normal(0.0, 1.0, (height, width)).astype(np.float32)
    shade = 1.0 + (coarse - 0.5) * 0.10 + fine * 0.018
    return PARCHMENT[None, None, :] * shade[:, :, None]


def render_plan(map_file: str, out_png: Path) -> dict | None:
    path = find_map(map_file)
    payload = load(map_file)
    if payload is None or path is None:
        return None

    floors = []
    walls = []
    for face in payload['faces']:
        if not drawn(face):
            continue
        points = face_points(payload, face)
        if len(points) < 2:
            continue
        if face['facet_type'] in FLOORS and len(points) >= 3:
            floors.append((face, points))
        elif face['facet_type'] == WALL:
            walls.append((face, points))
    if not floors:
        return None

    xs = [p[0] for _, points in floors for p in points]
    ys = [p[1] for _, points in floors for p in points]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    span = max(max_x - min_x, max_y - min_y, 1)
    pad = span * MARGIN
    min_x, max_x, min_y, max_y = min_x - pad, max_x + pad, min_y - pad, max_y + pad
    scale = LONG_SIDE / max(max_x - min_x, max_y - min_y)
    width = max(1, round((max_x - min_x) * scale))
    height = max(1, round((max_y - min_y) * scale))
    big = scale * SUPERSAMPLE
    big_w, big_h = width * SUPERSAMPLE, height * SUPERSAMPLE

    def to_px(point):
        return ((point[0] - min_x) * big, (max_y - point[1]) * big)

    # Height ranks: the share of the floor area lying lower, so a deep pit does not flatten every other storey.
    def area(points):
        total = 0.0
        for i in range(len(points)):
            x1, y1 = points[i][:2]
            x2, y2 = points[(i + 1) % len(points)][:2]
            total += x1 * y2 - x2 * y1
        return abs(total) / 2

    levels = sorted((sum(p[2] for p in points) / len(points), area(points)) for _, points in floors)
    level_z = [z for z, _ in levels]
    cumulative = np.cumsum([a for _, a in levels])
    total_area = cumulative[-1] if cumulative[-1] > 0 else 1.0

    def rank(z):
        index = bisect_right(level_z, z) - 1
        return float(cumulative[index] / total_area) if index >= 0 else 0.0

    doors = door_faces(payload, path)

    # Floor edges by their plan position: an edge no other floor shares outlines a room or a ledge; one shared with a
    # floor at another height is a step, drawn faint; one shared at the same height (a cave's slope split into
    # pieces, a room split by a portal) is not drawn.
    vertices = payload['vertices']
    edge_heights: dict[tuple, list[float]] = {}

    def floor_edges(face):
        ids = face['vertex_indices']
        for i in range(len(ids)):
            a, b = ids[i], ids[(i + 1) % len(ids)]
            if a < len(vertices) and b < len(vertices):
                pa, pb = vertices[a], vertices[b]
                key = tuple(sorted(((pa['x'], pa['y']), (pb['x'], pb['y']))))
                if key[0] != key[1]:
                    yield key, (pa['z'] + pb['z']) / 2

    for face, _ in floors:
        for key, z in floor_edges(face):
            edge_heights.setdefault(key, []).append(z)

    def outline(face):
        for key, _ in floor_edges(face):
            heights = edge_heights[key]
            if len(heights) == 1:
                yield key, False
            elif max(heights) - min(heights) > 8:
                yield key, True

    # Each storey's floors, then their outlines and its door walls, from low to high: higher storeys cover lower ones.
    items = []
    for face, points in floors:
        z = sum(p[2] for p in points) / len(points)
        items.append((z, 0, face, points))
        items.append((z, 1, face, points))
    for face, points in walls:
        if face['index'] in doors:
            items.append((min(p[2] for p in points) + 1, 2, face, points))
    items.sort(key=lambda item: (item[0], item[1]))

    mask = Image.new('L', (big_w, big_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    for _, kind, _, points in items:
        if kind == 0:
            mask_draw.polygon([to_px(p) for p in points], fill=255)

    plan = Image.new('RGB', (big_w, big_h))
    plan_draw = ImageDraw.Draw(plan)
    ink_width = max(2, round(1.4 * SUPERSAMPLE))
    for z, kind, face, points in items:
        if kind == 0:
            t = rank(z)
            colour = FLOOR_LOW + (FLOOR_HIGH - FLOOR_LOW) * (0.1 + 0.9 * t)
            if face['attributes'] & LAVA:
                colour = colour * 0.45 + LAVA_TINT * 0.55
            elif face['attributes'] & FLUID:
                colour = colour * 0.4 + WATER * 0.6
            fill = tuple(int(c) for c in colour)
            pixels = [to_px(p) for p in points]
            plan_draw.polygon(pixels, fill=fill, outline=fill)
        elif kind == 1:
            for (a, b), step in outline(face):
                plan_draw.line((to_px(a), to_px(b)), fill=STEP_INK if step else INK,
                               width=max(1, ink_width // 2) if step else ink_width)
        else:
            pixels = [to_px(p) for p in points]
            ends = max(((a, b) for a in pixels for b in pixels),
                       key=lambda pair: (pair[0][0] - pair[1][0]) ** 2 + (pair[0][1] - pair[1][1]) ** 2)
            plan_draw.line(ends, fill=DOOR_INK, width=ink_width * 2)

    # Only the drawing is supersampled; the parchment and its shading are composed at the final size.
    plan = plan.resize((width, height), Image.LANCZOS)
    mask = mask.resize((width, height), Image.LANCZOS)
    background = parchment(width, height, zlib.crc32(map_file.lower().encode()))
    glow = np.asarray(mask.filter(ImageFilter.GaussianBlur(7)), dtype=np.float32)[:, :, None] / 255.0
    glow = np.clip(glow * 1.8, 0, 1)
    background = background * (1 - glow * 0.85) + np.array(HALO, dtype=np.float32) * glow * 0.85
    edge = np.asarray(mask.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32)[:, :, None] / 255.0
    inside = np.asarray(mask, dtype=np.float32)[:, :, None] / 255.0
    rooms = np.asarray(plan, dtype=np.float32)
    # Burnt rim just inside the floors, as on hand-drawn maps.
    rooms = rooms * (0.78 + 0.22 * np.clip(edge * 1.6 - 0.6, 0, 1))
    image = background * (1 - inside) + rooms * inside
    result = Image.fromarray(np.clip(image, 0, 255).astype(np.uint8))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_png)
    return {'w': width, 'h': height, 'bounds': [round(min_x), round(min_y), round(max_x), round(max_y)]}


def floor_area(map_path: Path) -> float:
    """The walkable floor area of an indoor map (any world's BLV, MM9's rebuilt maps included), in square world
    units: the drawn floor faces projected from above."""
    payload = parse_blv_file(map_path)['payload']
    total = 0.0
    for face in payload['faces']:
        if face['facet_type'] not in FLOORS or not drawn(face):
            continue
        points = face_points(payload, face)
        if len(points) >= 3:
            total += abs(sum(points[i][0] * points[i - 1][1] - points[i - 1][0] * points[i][1]
                             for i in range(len(points)))) / 2
    return total


def to_uv(plan: dict, x: float, y: float) -> tuple[float, float]:
    min_x, min_y, max_x, max_y = plan['bounds']
    return (x - min_x) / (max_x - min_x), (max_y - y) / (max_y - min_y)


def all_maps() -> list[str]:
    return sorted(path.name for world in WORLD_IDS for path in (WORLDS / world / 'maps').glob('*.blv'))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--out', type=Path, required=True, help='folder for the PNG plans')
    parser.add_argument('--only', nargs='*', help='map files to draw (default: every MM6-MM8 indoor map)')
    parser.add_argument('--debug-events', action='store_true', help='mark every event point with a red dot')
    args = parser.parse_args()

    started = time.time()
    failed = []
    for map_file in args.only or all_maps():
        out_png = args.out / f'{Path(map_file).stem}.png'
        plan = render_plan(map_file, out_png)
        if plan is None:
            failed.append(map_file)
            continue
        if args.debug_events:
            image = Image.open(out_png).convert('RGB')
            draw = ImageDraw.Draw(image)
            for event, points in indoor_event_points(map_file).items():
                for x, y, _ in points:
                    u, v = to_uv(plan, x, y)
                    cx, cy = u * plan['w'], v * plan['h']
                    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(220, 0, 0))
                    draw.text((cx + 5, cy - 6), str(event), fill=(160, 0, 0))
            image.save(out_png)
        print(f'{map_file}: {plan["w"]}x{plan["h"]} bounds {plan["bounds"]}')
    print(f'{len(args.only or all_maps()) - len(failed)} plans in {time.time() - started:.1f} s')
    for map_file in failed:
        print(f'  no floors: {map_file}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
