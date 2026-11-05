#!/usr/bin/env python3
"""Find holes in an indoor map: places no face covers, where the view runs out of the drawn sectors (a portal that
does not cover its opening, two rooms meeting with no portal, missing or dropped faces, cracks).

The game runs with the hole view ([debug] indoor_hole_view: the main view clears to magenta, an open sky's faces draw
as faces, no sky pass, fog or view distance), and a screenshot tour stands the camera on a grid over the floors the
party can reach from its start points (the walkability audit's walk graph; --all-floors: every walkable floor),
where the party can stand (its height free over the floor, no wall within its radius: a camera inside a wall's
thickness sees magenta the party never can), looking four ways level and two ways up. A shot with magenta pixels shows a hole; the shots are
grouped into clusters by position and written to <out>/report.json with a contact sheet of the worst
(<out>/holes_sheet.jpg, the magenta marked in green).

    python3 tools/indoor_hole_sweep.py --world mm9 --map thjorgardcity.blv \\
        --assets "$PWD/output/mm9_rework/assets_dev" --out output/hole_sweep/thjorgardcity [--spacing 640]

Faster checks: --limit N shots, --chunk shots per game run. Works for any BLV (MM6-MM8 too); MM6-MM8 maps have no
open sky, so their sky faces draw as always.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from util.map_export import parse_blv_file  # noqa: E402

PARTY_RADIUS = 37.0          # the party's collision radius: sample points keep this far from walls and floor edges
PARTY_HEIGHT = 192.0         # free room a reachable point needs over it (the party's height)
FLOOR_NORMAL_Z = 0.7         # walkable: up-facing, at most about 45 degrees
MAGENTA_MIN = 25             # magenta pixels for a shot to count (single pixels are crack sparkle)
LEVEL_YAWS = 4
UP_YAWS = 2
UP_PITCH = math.radians(30.0)


def floor_points(blv: dict, spacing: float) -> list[tuple[float, float, float, int]]:
    """Points on a grid over the walkable floors: (x, y, z, sector), one per grid cell and height band."""
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    points, seen = [], set()
    for face in blv["faces"]:
        if face["is_portal"] or face["room_number"] <= 0 or len(face["vertex_indices"]) < 3:
            continue
        polygon = vertices[list(face["vertex_indices"])]
        normal = np.cross(polygon - polygon.mean(0), np.roll(polygon, -1, 0) - polygon.mean(0)).sum(0)
        length = np.linalg.norm(normal)
        if length < 1e-6 or normal[2] / length < FLOOR_NORMAL_Z:
            continue
        normal /= length
        flat = polygon[:, :2]
        low, high = flat.min(0), flat.max(0)
        xs = np.arange(math.ceil(low[0] / spacing) * spacing, high[0], spacing)
        ys = np.arange(math.ceil(low[1] / spacing) * spacing, high[1], spacing)
        candidates = [(x, y) for x in xs for y in ys] or [tuple(flat.mean(0))]
        for x, y in candidates:
            if not inside(flat, x, y) or edge_distance(flat, x, y) < PARTY_RADIUS:
                continue
            z = polygon[0, 2] - (normal[0] * (x - polygon[0, 0]) + normal[1] * (y - polygon[0, 1])) / normal[2]
            key = (round(x / spacing), round(y / spacing), round(z / 192.0))
            if key in seen:
                continue
            seen.add(key)
            points.append((float(x), float(y), float(z), int(face["room_number"])))
    return points


def reachable_points(blv_path: Path, spacing: float) -> list[tuple[float, float, float, int]]:
    """Points on the floors the party can reach: the walk graph of the shared walkability audit
    (level_generation/projects/hesper_stage/check_walkability.py: floors rastered in cells, joined within a step, doors
    open), the regions reachable from any party start point; one point per grid cell and height band. Floors outside
    the playable area (pockets beyond a city wall, floors under other floors) are left out."""
    sys.path.insert(0, str(ROOT / "level_generation/projects/hesper_stage"))
    import check_walkability as walk
    level = walk.load(blv_path)
    graph = walk.Graph(level)
    scene_text = blv_path.with_suffix(".scene.yml").read_text()
    try:
        scene = json.loads(scene_text)
    except json.JSONDecodeError:
        import yaml
        scene = yaml.safe_load(scene_text)
    regions = set()
    for start in scene.get("party_start_points") or []:
        x, y, z = start["position"]
        node = graph.node_near(x, y, z, tolerance=48)
        if node is not None:
            regions |= graph.reachable(graph.region[node])
    ceilings = ceiling_faces(blv_path)
    walls = WallGrid(blv_path)
    points, seen = [], set()
    for node, region in enumerate(graph.region):
        if region not in regions:
            continue
        x, y = walk.centre_of(graph.cell[node])
        z = graph.z[node]
        key = (round(x / spacing), round(y / spacing), round(z / 192.0))
        if key in seen or headroom(ceilings, x, y, z) < PARTY_HEIGHT or walls.too_close(x, y, z):
            continue
        seen.add(key)
        points.append((float(x), float(y), float(z), int(graph.face[node].sector)))
    return points


class WallGrid:
    """The walls (not portals, steeper than a walkable slope) in 256-unit plan cells, for the clearance test: the walk
    graph's cells run under walls (an upper floor's slab reaches into the wall's thickness), and a camera inside a wall
    sees past its faces into the clear colour, a hole the party can never see."""
    CELL = 256.0

    def __init__(self, blv_path: Path):
        payload = parse_blv_file(blv_path)["payload"]
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in payload["vertices"]], float)
        self.faces = []
        self.cells = {}
        for face in payload["faces"]:
            if face["is_portal"] or len(face["vertex_indices"]) < 3:
                continue
            polygon = vertices[list(face["vertex_indices"])]
            normal = np.cross(polygon - polygon.mean(0), np.roll(polygon, -1, 0) - polygon.mean(0)).sum(0)
            length = np.linalg.norm(normal)
            if length < 1e-6 or abs(normal[2] / length) >= FLOOR_NORMAL_Z:
                continue
            index = len(self.faces)
            self.faces.append((polygon, normal / length))
            low = np.floor((polygon.min(0)[:2] - PARTY_RADIUS) / self.CELL).astype(int)
            high = np.floor((polygon.max(0)[:2] + PARTY_RADIUS) / self.CELL).astype(int)
            for cx in range(low[0], high[0] + 1):
                for cy in range(low[1], high[1] + 1):
                    self.cells.setdefault((cx, cy), []).append(index)

    def too_close(self, x: float, y: float, z: float) -> bool:
        """Whether a wall comes nearer than the party's radius to its body (knee to eye height) standing here."""
        cell = (int(math.floor(x / self.CELL)), int(math.floor(y / self.CELL)))
        for height in (48.0, 104.0, 160.0):
            point = np.array([x, y, z + height])
            for index in self.cells.get(cell, ()):
                if polygon_distance(point, *self.faces[index]) < PARTY_RADIUS:
                    return True
        return False


def polygon_distance(point: np.ndarray, polygon: np.ndarray, normal: np.ndarray) -> float:
    """Distance from a point to a convex planar polygon."""
    depth = float(normal @ (point - polygon[0]))
    projected = point - depth * normal
    edge_best, inside_all = math.inf, True
    for i in range(len(polygon)):
        a, b = polygon[i], polygon[(i + 1) % len(polygon)]
        edge = b - a
        span = float(edge @ edge)
        if span < 1e-9:
            continue
        if float(np.cross(edge, projected - a) @ normal) < 0:
            inside_all = False
        t = min(max(float((projected - a) @ edge) / span, 0.0), 1.0)
        edge_best = min(edge_best, float(np.linalg.norm(projected - (a + t * edge))))
    return abs(depth) if inside_all else math.hypot(depth, edge_best)


def ceiling_faces(blv_path: Path) -> list:
    """The down-facing faces (ceilings, undersides): (polygon xy, plane point, normal, xy bounds)."""
    payload = parse_blv_file(blv_path)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in payload["vertices"]], float)
    faces = []
    for face in payload["faces"]:
        if face["is_portal"] or len(face["vertex_indices"]) < 3:
            continue
        polygon = vertices[list(face["vertex_indices"])]
        normal = np.cross(polygon - polygon.mean(0), np.roll(polygon, -1, 0) - polygon.mean(0)).sum(0)
        length = np.linalg.norm(normal)
        if length < 1e-6 or normal[2] / length > -0.3:
            continue
        faces.append((polygon[:, :2], polygon[0], normal / length, polygon[:, :2].min(0), polygon[:, :2].max(0)))
    return faces


def headroom(ceilings: list, x: float, y: float, z: float) -> float:
    """The room over a floor point up to the lowest ceiling over it (a gallery under a sloping roof, the top of a
    slab: the party cannot stand there)."""
    best = math.inf
    for flat, point, normal, low, high in ceilings:
        if not (low[0] <= x <= high[0] and low[1] <= y <= high[1]) or not inside(flat, x, y):
            continue
        height = point[2] - (normal[0] * (x - point[0]) + normal[1] * (y - point[1])) / normal[2]
        if height > z + 1.0:
            best = min(best, height - z)
    return best


def inside(polygon: np.ndarray, x: float, y: float) -> bool:
    result, j = False, len(polygon) - 1
    for i in range(len(polygon)):
        (xi, yi), (xj, yj) = polygon[i], polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            result = not result
        j = i
    return result


def edge_distance(polygon: np.ndarray, x: float, y: float) -> float:
    p = np.array([x, y])
    best = math.inf
    for i in range(len(polygon)):
        a, b = polygon[i], polygon[(i + 1) % len(polygon)]
        d = b - a
        t = np.clip((p - a) @ d / max(d @ d, 1e-9), 0.0, 1.0)
        best = min(best, float(np.linalg.norm(a + t * d - p)))
    return best


def shots_for(points: list) -> list[dict]:
    shots = []
    for index, (x, y, z, sector) in enumerate(points):
        offset = (index * 0.618034) % 1.0 * (2 * math.pi / LEVEL_YAWS)   # turn each point's fan a little
        for k in range(LEVEL_YAWS):
            shots.append({"name": f"p{index:05d}_l{k}", "position": [x, y, z], "yaw": offset + k * 2 * math.pi / LEVEL_YAWS,
                          "pitch": 0.0, "sector": sector})
        for k in range(UP_YAWS):
            shots.append({"name": f"p{index:05d}_u{k}", "position": [x, y, z],
                          "yaw": offset + math.pi / 4 + k * 2 * math.pi / UP_YAWS, "pitch": UP_PITCH, "sector": sector})
    return shots


def run_chunk(args, chunk: list[dict], folder: Path, index: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    tour = folder / "tour.yml"
    import yaml
    tour.write_text(yaml.safe_dump({"output_dir": str(folder.resolve()), "settle_seconds": args.settle, "exit": True,
                                    "shots": [{k: v for k, v in s.items() if k != "sector"} for s in chunk]},
                                   sort_keys=False))
    first = chunk[0]
    command = ["./tools/run_game.sh", "--isolated", f"hole_sweep_{Path(args.map).stem}_{index}", "--world", args.world,
               "--map", args.map, "--position", *[str(v) for v in first["position"]],
               "--yaw-radians", str(first["yaw"]), "--pitch-degrees", "0", "--warmup", "3",
               "--seconds", str(int(40 + len(chunk) * (args.settle + 0.25))),
               "--set", "debug.indoor_hole_view=true", "--set", f"debug.screenshot_tour_path={tour.resolve()}",
               "--set", "video.bloom=false", "--set", "video.ambient_occlusion=false",
               "--set", "video.cinematic_grading=false", "--set", "video.antialiasing=off"]
    if args.assets:
        command += ["--assets", args.assets]
    subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                   env={**__import__("os").environ, "SDL_AUDIODRIVER": "dummy"})


def magenta(image: np.ndarray) -> np.ndarray:
    r, g, b = image[..., 0].astype(int), image[..., 1].astype(int), image[..., 2].astype(int)
    return (r > 170) & (b > 170) & (g < 90) & (np.abs(r - b) < 70)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--world", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--assets", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--spacing", type=float, default=640.0)
    parser.add_argument("--chunk", type=int, default=600)
    parser.add_argument("--settle", type=float, default=0.15)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--analyse-only", action="store_true")
    parser.add_argument("--all-floors", action="store_true",
                        help="sample every walkable floor, not only those reachable from the party start")
    args = parser.parse_args()
    out = Path(args.out)
    root = Path(args.assets) if args.assets else ROOT / "assets_dev"
    blv = parse_blv_file(root / "worlds" / args.world / "maps" / args.map)["payload"]
    blv_path = root / "worlds" / args.world / "maps" / args.map
    points = floor_points(blv, args.spacing) if args.all_floors else reachable_points(blv_path, args.spacing)
    shots = shots_for(points)
    if args.limit:
        shots = shots[:args.limit]
    print(f"{len(shots)} shots", flush=True)
    chunks = [shots[i:i + args.chunk] for i in range(0, len(shots), args.chunk)]
    if not args.analyse_only:
        for index, chunk in enumerate(chunks):
            run_chunk(args, chunk, out / f"chunk{index:02d}", index)
            print(f"chunk {index + 1}/{len(chunks)} done", flush=True)
    found, missing = [], 0
    for index, chunk in enumerate(chunks):
        folder = out / f"chunk{index:02d}"
        for order, shot in enumerate(chunk, 1):
            path = folder / f"{order:02d}-{shot['name']}.png" if order < 10 else folder / f"{order}-{shot['name']}.png"
            if not path.exists():
                missing += 1
                continue
            image = np.asarray(Image.open(path).convert("RGB"))
            mask = magenta(image)
            count = int(mask.sum())
            if count >= MAGENTA_MIN:
                ys, xs = np.nonzero(mask)
                # An area hole (an opening, a missing face) keeps pixels when the mask shrinks by one; a crack (a line
                # one or two pixels wide along a seam) does not.
                solid = int(ndimage.binary_erosion(mask, iterations=1).sum())
                found.append(dict(shot, pixels=count, area_pixels=solid, kind="hole" if solid >= 9 else "crack",
                                  box=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], image=str(path)))
    # Clusters: shots of one kind within two grid steps of each other, holes first.
    clusters = []
    for hit in sorted(found, key=lambda h: (h["kind"] != "hole", -h["area_pixels"], -h["pixels"])):
        p = np.array(hit["position"][:2])
        for cluster in clusters:
            if cluster["kind"] == hit["kind"] and np.linalg.norm(p - cluster["centre"]) <= 2 * args.spacing:
                cluster["shots"].append(hit)
                break
        else:
            clusters.append({"centre": p, "kind": hit["kind"], "shots": [hit]})
    report = {"map": args.map, "shots": len(shots), "missing_images": missing, "shots_with_holes": len(found),
              "shots_with_area_holes": sum(1 for h in found if h["kind"] == "hole"),
              "clusters": [{"kind": c["kind"], "centre": c["centre"].round().tolist(), "shots": len(c["shots"]),
                            "worst_pixels": c["shots"][0]["pixels"], "sectors": sorted({s["sector"] for s in c["shots"]}),
                            "worst": {k: c["shots"][0][k] for k in ("name", "position", "yaw", "pitch", "box", "image")}}
                           for c in clusters]}
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"{len(found)} of {len(shots)} shots show magenta ({report['shots_with_area_holes']} area holes), "
          f"{sum(1 for c in clusters if c['kind'] == 'hole')} hole and {sum(1 for c in clusters if c['kind'] == 'crack')} "
          f"crack clusters; {missing} images missing")
    worst = [c["shots"][0] for c in clusters[:24]]
    if worst:
        w, h = 480, 270
        sheet = Image.new("RGB", (w * 4, h * ((len(worst) + 3) // 4)))
        for k, hit in enumerate(worst):
            image = np.asarray(Image.open(hit["image"]).convert("RGB")).copy()
            image[magenta(image)] = [0, 255, 0]
            tile = Image.fromarray(image).resize((w, h))
            ImageDraw.Draw(tile).text((6, 6), f"{hit['kind']} {hit['name']} {hit['pixels']}px "
                                      f"({hit['position'][0]:.0f}, {hit['position'][1]:.0f}, {hit['position'][2]:.0f})",
                                      fill=(255, 255, 0))
            sheet.paste(tile, ((k % 4) * w, (k // 4) * h))
        sheet.save(out / "holes_sheet.jpg", quality=85)


if __name__ == "__main__":
    main()
