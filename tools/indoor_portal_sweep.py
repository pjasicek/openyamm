#!/usr/bin/env python3
"""Check an indoor map's portals for clipping: the camera standing in each portal, and just in front of and behind it,
looking through it both ways, across it and along it, with the hole view on ([debug] indoor_hole_view: the main view
clears to magenta, an open sky draws as faces, no fog or view distance), so a pixel no drawn face covers shows magenta.

A portal is the BLV's portal faces between one pair of sectors in one plane. Its poses (a screenshot tour, run in
chunks like tools/indoor_hole_sweep.py):
- a vertical portal (a doorway, an arch, a street's cut): up to three points across its width, each within one of
  its faces and 80 units in from that face's sides (one sector pair's faces in one plane may be two doorways with a
  pier between them), each with the party on the floor under it (or the camera at the opening's middle height when
  no floor is near its bottom: a window), at -24, 0 and +24 units along the portal's normal; at each, eight level
  yaws (through it both ways, both ways 50 degrees off, both ways along it) and, in the plane, through it both ways
  looking 40 degrees up and down;
- a horizontal portal (a stairwell, a hole in a floor, a city's sky cut): up to three points over its faces, the
  camera 24 units under, in and 24 units over its plane, four level yaws and two looking 60 degrees up and down.

A shot with at least MAGENTA_MIN magenta pixels shows something undrawn; each such shot is taken again with the
portal culling off (`portals culling off`: every sector through the camera's frustum). Per portal: `clipping` when a
shot loses at least MAGENTA_MIN magenta pixels without the culling (the portal culling dropped what the camera sees),
`hole` when the magenta stays (the map's own hole, or a pose outside the map), else clean. The report
(<out>/report.json, <out>/portals.tsv) lists each portal; clipping_sheet.jpg and hole_sheet.jpg show the worst shots.

    python3 tools/indoor_portal_sweep.py --world mm9 --map klusoshouse.blv --out output/portal_sweep/klusoshouse \\
        [--assets "$PWD/output/mm9_rework/assets_dev"] [--analyse-only]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from util.map_export import parse_blv_file  # noqa: E402
from indoor_hole_sweep import magenta, run_chunk  # noqa: E402

EYE_HEIGHT = 152.0          # MM9's party eye height (world.yml partyMovement.eyeHeight); --eye for other worlds
EDGE_INSET = 80.0           # points keep this far in from a face's sides (a converted map's faces run 41 into jambs)
MAX_POINTS = 3              # points per portal
OFFSETS = (-24.0, 0.0, 24.0)
MAGENTA_MIN = 25
FLOOR_NORMAL_Z = 0.7


class Floors:
    def __init__(self, vertices: np.ndarray, faces: list):
        tris = []
        for face in faces:
            if face["is_portal"]:
                continue
            idx = face["vertex_indices"][:face["vertex_per_face_count"]]
            if len(idx) < 3:
                continue
            poly = vertices[idx]
            normal = np.cross(poly[1] - poly[0], poly[2] - poly[0])
            length = np.linalg.norm(normal)
            if length < 1e-6 or normal[2] / length < FLOOR_NORMAL_Z:
                continue
            tris += [(poly[0], poly[k], poly[k + 1]) for k in range(1, len(poly) - 1)]
        self.tris = np.array(tris, float).reshape(-1, 3, 3)
        self.low, self.high = self.tris.min(1), self.tris.max(1)

    def below(self, x: float, y: float, z_top: float) -> float | None:
        near = (self.low[:, 0] <= x) & (self.high[:, 0] >= x) & (self.low[:, 1] <= y) & (self.high[:, 1] >= y)
        best = None
        for a, b, c in self.tris[near]:
            v0, v1, p = b - a, c - a, np.array([x, y]) - a[:2]
            den = v0[0] * v1[1] - v0[1] * v1[0]
            if abs(den) < 1e-9:
                continue
            u = (p[0] * v1[1] - p[1] * v1[0]) / den
            v = (v0[0] * p[1] - v0[1] * p[0]) / den
            if u < -1e-4 or v < -1e-4 or u + v > 1 + 1e-4:
                continue
            z = a[2] + u * v0[2] + v * v1[2]
            if z <= z_top + 1.0 and (best is None or z > best):
                best = z
        return best


def portals(blv: dict) -> list[dict]:
    """The portals: portal faces grouped by sector pair and plane, with their vertices, normal and extent."""
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    groups = defaultdict(list)
    for face in blv["faces"]:
        if not face["is_portal"]:
            continue
        idx = face["vertex_indices"][:face["vertex_per_face_count"]]
        if len(idx) < 3:
            continue
        poly = vertices[idx]
        normal = np.cross(poly - poly.mean(0), np.roll(poly, -1, 0) - poly.mean(0)).sum(0)
        length = np.linalg.norm(normal)
        if length < 1e-6:
            continue
        normal /= length
        for k in range(3):                                   # one sign for both sides' faces of the same plane
            if abs(normal[k]) > 1e-3:
                if normal[k] < 0:
                    normal = -normal
                break
        pair = tuple(sorted((int(face["room_number"]), int(face["room_behind_number"]))))
        key = (pair, tuple(np.round(normal, 2)), round(float(normal @ poly[0]) / 8.0))
        groups[key].append((face["index"], poly, normal))
    result = []
    for (pair, _, _), members in groups.items():
        points = np.vstack([p for _, p, _ in members])
        normal = members[0][2]
        result.append({"id": len(result), "sectors": list(pair), "faces": [i for i, _, _ in members],
                       "polygons": [poly for _, poly, _ in members],
                       "points": points, "normal": normal, "centre": points.mean(0),
                       "vertical": abs(normal[2]) < 0.5})
    return result


def spread(lo: float, hi: float) -> list[float]:
    """Up to MAX_POINTS positions across [lo, hi], EDGE_INSET in from both ends (the middle of a narrow one)."""
    a, b = lo + EDGE_INSET, hi - EDGE_INSET
    if b <= a:
        return [(lo + hi) / 2]
    count = min(MAX_POINTS, max(1, int((b - a) // 384) + 1))
    return [(a + b) / 2] if count == 1 else list(np.linspace(a, b, count))


def spread_members(intervals: list[tuple[float, float]]) -> list[float]:
    """Up to MAX_POINTS positions over a portal's member faces, each within one face (spread): the faces of one sector
    pair in one plane may be two doorways with a pier between them, whose middle is in the wall (Verhoffin Ruins)."""
    found = sorted(set(round(v, 1) for lo, hi in intervals for v in spread(lo, hi)))
    if len(found) <= MAX_POINTS:
        return found
    return [found[int(round(k))] for k in np.linspace(0, len(found) - 1, MAX_POINTS)]


def inside_any(polygons: list, x: float, y: float) -> bool:
    """(x, y) inside one of the polygons' outlines (a horizontal portal's member faces)."""
    for poly in polygons:
        inside, ring = False, poly[:, :2]
        for a in range(len(ring)):
            x1, y1 = ring[a]
            x2, y2 = ring[(a + 1) % len(ring)]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
        if inside:
            return True
    return False


def label(offset: float) -> str:
    """A tour shot name takes letters, digits, '_' and '-': m24, 0, p24."""
    return ("m" if offset < 0 else "p" if offset > 0 else "") + str(abs(int(offset)))


def portal_shots(portal: dict, floors: Floors, eye: float) -> list[dict]:
    shots = []
    n, pts = portal["normal"], portal["points"]
    pid = portal["id"]
    if portal["vertical"]:
        facing = math.atan2(n[1], n[0])
        u = np.array([-n[1], n[0], 0.0]) / (np.hypot(n[0], n[1]) or 1.0)
        z_lo, z_hi = float(pts[:, 2].min()), float(pts[:, 2].max())
        intervals = [(float((poly @ u).min()), float((poly @ u).max())) for poly in portal["polygons"]]
        for k, s in enumerate(spread_members(intervals)):
            base = portal["centre"] + u * (s - float(portal["centre"] @ u))
            for offset in OFFSETS:
                p = base + n * offset
                floor = floors.below(float(p[0]), float(p[1]), z_lo + 48.0)
                if floor is not None and floor >= z_lo - 64.0 and floor + eye < z_hi - 8.0:
                    foot = floor
                else:
                    foot = (z_lo + z_hi) / 2 - eye                       # an opening off the floor: its middle
                position = [round(float(p[0]), 1), round(float(p[1]), 1), round(float(foot), 1)]
                yaws = [facing, facing + math.pi, facing + math.radians(50), facing - math.radians(50),
                        facing + math.pi + math.radians(50), facing + math.pi - math.radians(50),
                        facing + math.pi / 2, facing - math.pi / 2]
                poses = [(y, 0.0) for y in yaws]
                if offset == 0.0:
                    poses += [(facing, 40.0), (facing, -40.0), (facing + math.pi, 40.0), (facing + math.pi, -40.0)]
                for j, (yaw, pitch) in enumerate(poses):
                    shots.append({"name": f"q{pid:04d}_s{k}_o{label(offset)}_{j:02d}", "position": position,
                                  "yaw": round(yaw % (2 * math.pi), 4), "pitch": round(math.radians(pitch), 4),
                                  "portal": pid, "offset": offset})
    else:
        plane = float(portal["centre"][2])
        xs, ys = pts[:, 0], pts[:, 1]
        samples = [(float(x), float(y)) for x in spread(float(xs.min()), float(xs.max()))
                   for y in spread(float(ys.min()), float(ys.max()))
                   if inside_any(portal["polygons"], float(x), float(y))]
        if not samples:                                      # an outline the grid misses: its members' centres
            samples = [(float(poly[:, 0].mean()), float(poly[:, 1].mean())) for poly in portal["polygons"]]
        samples = samples[:MAX_POINTS]
        for k, (x, y) in enumerate(samples):
            for offset in OFFSETS:
                position = [round(x, 1), round(y, 1), round(plane + offset - eye, 1)]
                poses = [(i * math.pi / 2, 0.0) for i in range(4)] + [(0.3, 60.0), (0.3, -60.0)]
                for j, (yaw, pitch) in enumerate(poses):
                    shots.append({"name": f"q{pid:04d}_s{k}_o{label(offset)}_{j:02d}", "position": position,
                                  "yaw": round(yaw, 4), "pitch": round(math.radians(pitch), 4),
                                  "portal": pid, "offset": offset})
    return shots


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--world", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--assets", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--eye", type=float, default=EYE_HEIGHT)
    parser.add_argument("--chunk", type=int, default=600)
    parser.add_argument("--settle", type=float, default=0.15)
    parser.add_argument("--analyse-only", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assets = Path(args.assets) if args.assets else ROOT / "assets_dev"
    blv = parse_blv_file(assets / "worlds" / args.world / "maps" / args.map)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    floors = Floors(vertices, blv["faces"])
    found = portals(blv)
    shots = [s for p in found for s in portal_shots(p, floors, args.eye)]
    chunks = [shots[i:i + args.chunk] for i in range(0, len(shots), args.chunk)]
    def done(folder: Path, chunk: list) -> bool:
        return all((folder / f"{number:02d}-{shot['name']}.png").exists() for number, shot in enumerate(chunk, 1))

    if not args.analyse_only:
        for index, chunk in enumerate(chunks):
            if not done(out / f"chunk_{index:03d}", chunk):
                run_chunk(args, chunk, out / f"chunk_{index:03d}", index)

    def count(path: Path) -> int | None:
        return int(magenta(np.asarray(Image.open(path).convert("RGB"))).sum()) if path.exists() else None

    flagged = []                                          # (shot, image, magenta pixels) of the ordinary pass
    missing = defaultdict(int)
    for index, chunk in enumerate(chunks):
        folder = out / f"chunk_{index:03d}"
        for number, shot in enumerate(chunk, 1):
            image = folder / f"{number:02d}-{shot['name']}.png"
            pixels = count(image)
            if pixels is None:
                missing[shot["portal"]] += 1
            elif pixels >= MAGENTA_MIN:
                flagged.append((shot, image, pixels))

    # The reference pass: each flagged shot again with the portal culling off (`portals culling off`). Magenta that
    # goes is the portal culling's (clipping); magenta that stays is the map's own (a hole, or a pose outside the map).
    reference = [dict(shot, commands=["portals culling off"]) for shot, _, _ in flagged]
    reference_chunks = [reference[i:i + args.chunk] for i in range(0, len(reference), args.chunk)]
    if not args.analyse_only:
        for index, chunk in enumerate(reference_chunks):
            if not done(out / f"reference_{index:03d}", chunk):
                run_chunk(args, chunk, out / f"reference_{index:03d}", 1000 + index)
    reference_counts = {}
    for index, chunk in enumerate(reference_chunks):
        for number, shot in enumerate(chunk, 1):
            reference_counts[shot["name"]] = count(out / f"reference_{index:03d}" / f"{number:02d}-{shot['name']}.png")

    per = defaultdict(lambda: {"clipping": [], "hole": [], "unchecked": 0})
    for shot, image, pixels in flagged:
        ref = reference_counts.get(shot["name"])
        record = per[shot["portal"]]
        if ref is None:
            record["unchecked"] += 1
        elif pixels - ref >= MAGENTA_MIN:
            record["clipping"].append((pixels - ref, str(image), shot))
        else:
            record["hole"].append((pixels, str(image), shot))
    shots_per = defaultdict(int)
    for shot in shots:
        shots_per[shot["portal"]] += 1
    rows = []
    for portal in found:
        r = per[portal["id"]]
        status = "untested" if missing[portal["id"]] == shots_per[portal["id"]] else \
            "clipping" if r["clipping"] else "hole" if r["hole"] else "unchecked" if r["unchecked"] else "clean"
        offsets = sorted({c[2]["offset"] for c in r["clipping"]})
        rows.append({"portal": portal["id"], "sectors": portal["sectors"], "faces": portal["faces"],
                     "vertical": bool(portal["vertical"]), "centre": [round(float(v)) for v in portal["centre"]],
                     "shots": shots_per[portal["id"]], "missing": missing[portal["id"]],
                     "clipping_shots": len(r["clipping"]), "clipping_offsets": offsets, "hole_shots": len(r["hole"]),
                     "status": status,
                     "worst": max(r["clipping"], key=lambda c: c[0])[1] if r["clipping"] else
                     (max(r["hole"], key=lambda c: c[0])[1] if r["hole"] else None)})
    summary = {"map": args.map, "portals": len(found), "shots": len(shots), "reference_shots": len(reference),
               "missing": sum(missing.values()),
               "clipping_shots": sum(r["clipping_shots"] for r in rows),
               "hole_shots": sum(r["hole_shots"] for r in rows),
               "by_status": {s: sum(1 for r in rows if r["status"] == s)
                             for s in ("clean", "clipping", "hole", "unchecked", "untested")}}
    (out / "report.json").write_text(json.dumps({"summary": summary, "portals": rows}, indent=1) + "\n")
    with (out / "portals.tsv").open("w") as handle:
        handle.write("portal\tsectors\tvertical\tcentre\tshots\tmissing\tclipping_shots\tclipping_offsets"
                     "\thole_shots\tstatus\tworst\n")
        for r in rows:
            handle.write(f"{r['portal']}\t{r['sectors']}\t{r['vertical']}\t{r['centre']}\t{r['shots']}\t{r['missing']}"
                         f"\t{r['clipping_shots']}\t{r['clipping_offsets']}\t{r['hole_shots']}\t{r['status']}"
                         f"\t{r['worst']}\n")
    for kind in ("clipping", "hole"):
        worst = sorted((c for r in per.values() for c in r[kind]), key=lambda c: -c[0])[:16]
        if not worst:
            continue
        tiles = []
        for _, path, shot in worst:
            image = Image.open(path).convert("RGB")
            marked = np.asarray(image).copy()
            marked[magenta(marked)] = (0, 255, 0)
            tiles.append(Image.fromarray(marked).resize((480, 270)))
        sheet = Image.new("RGB", (480 * 4, 270 * ((len(tiles) + 3) // 4)))
        for k, tile in enumerate(tiles):
            sheet.paste(tile, ((k % 4) * 480, (k // 4) * 270))
        sheet.save(out / f"{kind}_sheet.jpg", quality=85)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
