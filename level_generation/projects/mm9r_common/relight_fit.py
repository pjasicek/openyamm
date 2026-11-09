#!/usr/bin/env python3
"""
Fit a dungeon's bake-profile scales to MM9's DAT lightmaps, per zone and per room, from the saved Cycles passes (no
Blender, no bake). Generalises mm9r_beethoven/work/relight/fit.py (the 2026-10-31 re-light of the pre-overnight maps).

    python3 level_generation/projects/mm9r_common/relight_fit.py level_generation/projects/mm9r_<map> \
        [--direct D] [--bounce B] [--ambient A] [--sky S] [--max M] [--level SECTOR=LEVEL ...] [--grid] [--rooms]

The composed lightmap is linear in the profile's scales (tools/lighting/bake_indoor.py compose):

    lighting = min(d*D + d*b*I + a*floor(sector) + s*(SD + sb*SI), max_lighting)

D/I are the lamps' direct and bounce passes, SD/SI the sky emitters' (when baked), floor(sector) the scene's sector
ambient (max(0.18, (31 - level) / 31 * 0.97)). The face -> page mapping comes from the installed sidecar (a recompose
keeps it). Missing options take the profile's values. `--level` overrides a sector's minimum light level (the
player-light stand-in floor) in the prediction only. Blurs are left out (they keep a chart's mean).

Zones come from the project's `hue_zones.py` / `dat_lightmaps.py` (boxes in MM9 units, y up), as hue_vs_lightmaps.py.
`--rooms` also prints every native room (sector): DAT polygons are given to the room of the nearest native face centre.
`--grid` searches direct x ambient (x sky when baked) for the least squared log luminance error over the zones plus
half the squared log B/R and G/R errors.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("hvl", ROOT / "level_generation/projects/mm9r_common/hue_vs_lightmaps.py")
hvl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hvl)
LUMA = hvl.LUMA
SCALE = hvl.SCALE
QUANTILES = (0.1, 0.5, 0.9)
CONTRAST = 0.5  # weight of the map-wide texel-luma quantiles in --grid (keeps the bake's contrast)
DEFAULTS = {"direct_scale": 1.0, "bounce_scale": 1.0, "ambient_scale": 0.5, "sky_scale": 1.0, "max_lighting": 4.0,
            "emitters": [], "ambient_colour": [1.0, 1.0, 1.0]}


def floor_of(level: int) -> float:
    return max(0.18, (31 - level) / 31 * 0.97)


def face_cells(face, record, shape):
    pts = np.array(face["points"], float)
    page, ua, va = record
    height, width = shape
    hom = np.c_[pts, np.ones(len(pts))]
    uv = np.stack([hom @ ua, hom @ va], 1) * [width, height]
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    grid = np.stack([xs.ravel(), ys.ravel()], 1)
    signs = np.array([(uv[(i + 1) % len(uv)][0] - uv[i][0]) * (grid[:, 1] - uv[i][1])
                      - (uv[(i + 1) % len(uv)][1] - uv[i][1]) * (grid[:, 0] - uv[i][0]) for i in range(len(uv))])
    inside = (signs >= -1e-6).all(0) | (signs <= 1e-6).all(0)
    cells = grid[inside].astype(int)
    if not len(cells):
        cells = np.array([[int(uv[:, 0].mean()), int(uv[:, 1].mean())]])
    cells[:, 0] = np.clip(cells[:, 0], 0, width - 1)
    cells[:, 1] = np.clip(cells[:, 1], 0, height - 1)
    return pts, cells


class Data:
    def __init__(self, project: Path):
        self.project = project
        settings = yaml.safe_load((project / "overrides.yml").read_text())["map"]
        self.stem = settings["stem"]
        offset = np.array(settings.get("offset", (0, 0, 0)), float)
        profile_path = ROOT / f"tools/lighting/baked_indoors/profiles/mm9_{self.stem}.yml"
        self.profile = dict(DEFAULTS, **json.loads(profile_path.read_text()))
        self.profile.setdefault("sky_bounce_scale", self.profile["bounce_scale"])
        bakes = ROOT / f"output/mm9_rework/bakes/{self.stem}"
        self.scene = json.loads((bakes / "scene.json").read_text())
        _pages, faces = hvl.read_pages_and_faces(ROOT / f"output/mm9_rework/assets_dev/worlds/mm9/maps/{self.stem}.lighting")
        assert len(faces) == self.scene["face_count"]
        pages = sorted({r[0] for r in faces if r is not None})
        terms = ["direct", "indirect"] + (["sky_direct", "sky_indirect"]
                                          if (bakes / "page_0_sky_direct.npy").exists() else [])
        self.has_sky = "sky_direct" in terms
        passes = {(p, t): np.load(bakes / f"page_{p}_{t}.npy", mmap_mode="r") for p in pages for t in terms}
        emitter_textures = {t.lower() for e in self.profile["emitters"] for t in e["textures"]}
        self.zones = hvl.load_zones(project)
        boxes = {n: (np.array(b[:3], float), np.array(b[3:], float)) for n, b in self.zones.items()}
        rows = {t: [] for t in terms}
        weight, sector, zone_of, centres = [], [], [], []
        for face in self.scene["faces"]:
            record = faces[face["index"]]
            if record is None or not face["visible"] or face["texture"].lower() in emitter_textures:
                continue
            shape = passes[(record[0], "direct")].shape[:2]
            pts, cells = face_cells(face, record, shape)
            for t in terms:
                rows[t].append(np.asarray(passes[(record[0], t)][cells[:, 1], cells[:, 0], :3], np.float32))
            n = len(cells)
            weight.append(np.full(n, hvl.polygon_area(pts) / SCALE ** 2 / n))
            centre = pts.mean(0)
            lt = np.array([centre[0] + offset[0], centre[2] + offset[2], centre[1] + offset[1]]) / SCALE
            centres.append(lt)
            sector.append(np.full(n, face["sector"]))
            zone_of.append([name for name, (lo, hi) in boxes.items() if (lt >= lo).all() and (lt <= hi).all()])
        self.face_len = np.array([len(w) for w in weight])
        self.terms = {t: np.concatenate(rows[t]) for t in terms}
        self.weight = np.concatenate(weight)
        self.sector = np.concatenate(sector)
        self.face_centres = np.array(centres)
        self.face_sector = np.array([s[0] for s in sector])
        starts = np.r_[0, np.cumsum(self.face_len)]
        self.zone_mask = {}
        for name in self.zones:
            mask = np.zeros(len(self.weight), bool)
            for i, z in enumerate(zone_of):
                if name in z:
                    mask[starts[i]:starts[i + 1]] = True
            self.zone_mask[name] = mask
        self.sector_floor = np.array(self.scene["sector_ambient"], float)
        self.colour = np.array(self.profile["ambient_colour"], np.float32)
        world = hvl.read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS" / settings.get("dat", f"{self.stem.upper()}.dat"))
        self.dat, _ = hvl.dat_texels(world, self.zones)
        # DAT polygons per native room: nearest native face centre.
        model = next(m for m in world.world_models if m.name == "PhysicsBSP")
        tree = cKDTree(self.face_centres)
        self.dat_rooms: dict = {}
        dat_lum, dat_w = [], []
        for poly in model.polies:
            pixels = getattr(poly, "lightmap_pixels_bgra", None)
            if not pixels:
                continue
            value = np.array(pixels, np.int64)
            texels = np.stack([(value >> 16) & 255, (value >> 8) & 255, value & 255], 1).astype(float) / 255
            pts = np.array([model.points[d.vertex_index] for d in poly.disk_verts], float)
            w = hvl.polygon_area(pts) / len(texels) if len(pts) >= 3 else 1.0
            dat_lum.append(texels @ LUMA)
            dat_w.append(np.full(len(texels), w))
            _, idx = tree.query(np.array(poly.center, float))
            room = int(self.face_sector[idx])
            entry = self.dat_rooms.setdefault(room, [np.zeros(3), 0.0])
            entry[0] += texels.sum(0) * w
            entry[1] += w * len(texels)
        lum, w = np.concatenate(dat_lum), np.concatenate(dat_w)
        self.dat_quantiles = np.array([hvl.wquantile(lum, w, q) for q in QUANTILES])

    def lit(self, d, b, a, s, sb, top, levels=None):
        floor = self.sector_floor[self.sector].copy()
        for sec, level in (levels or {}).items():
            floor[self.sector == sec] = floor_of(level)
        value = d * self.terms["direct"] + d * b * self.terms["indirect"] + a * floor[:, None] * self.colour
        if self.has_sky:
            value = value + s * (self.terms["sky_direct"] + sb * self.terms["sky_indirect"])
        return np.minimum(value, top)

    def mean(self, lit, mask):
        w = self.weight[mask]
        return (lit[mask] * w[:, None]).sum(0) / w.sum()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    for key in ("direct", "bounce", "ambient", "sky", "max"):
        ap.add_argument(f"--{key}", type=float)
    ap.add_argument("--ambient-colour", type=float, nargs=3, help="the profile's ambient_colour (floor tint)")
    ap.add_argument("--level", action="append", default=[], help="SECTOR=LEVEL (prediction only)")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--rooms", action="store_true")
    ap.add_argument("--skip", action="append", default=[], help="zones left out of --grid")
    args = ap.parse_args()
    data = Data(args.project.resolve())
    p = data.profile
    d = args.direct if args.direct is not None else p["direct_scale"]
    b = args.bounce if args.bounce is not None else p["bounce_scale"]
    a = args.ambient if args.ambient is not None else p["ambient_scale"]
    s = args.sky if args.sky is not None else p["sky_scale"]
    top = args.max if args.max is not None else p["max_lighting"]
    sb = p["sky_bounce_scale"] if args.bounce is None else b
    levels = {int(k): int(v) for k, v in (x.split("=") for x in args.level)}
    if args.ambient_colour:
        data.colour = np.array(args.ambient_colour, np.float32)
    if args.grid:
        return grid(data, b, sb, top, levels, set(args.skip))
    lit = data.lit(d, b, a, s, sb, top, levels)
    print(f"{data.stem}: direct {d} bounce {b} ambient {a} x {data.colour.tolist()} sky {s} (sky bounce {sb}) max {top}"
          + (f" levels {levels}" if levels else ""))
    print(f"{'zone':18s} {'MM9':>6s} {'B/R':>5s} {'G/R':>5s} | {'ours':>6s} {'ratio':>5s} {'B/R':>5s} {'G/R':>5s}")
    for name in data.zones:
        mask = data.zone_mask[name]
        if not mask.any() or not data.dat[name][0]:
            print(f"{name:18s} no data")
            continue
        mm9 = hvl.stats(data.dat[name])["mean"]
        ours = data.mean(lit, mask)
        print(f"{name:18s} {mm9 @ LUMA:6.3f} {mm9[2] / mm9[0]:5.2f} {mm9[1] / mm9[0]:5.2f} | {ours @ LUMA:6.3f} "
              f"{ours @ LUMA / (mm9 @ LUMA):5.2f} {ours[2] / ours[0]:5.2f} {ours[1] / ours[0]:5.2f}")
    lum = lit @ LUMA
    ours_q = [hvl.wquantile(lum, data.weight, q) for q in QUANTILES]
    print("map-wide texel luma p10/p50/p90: MM9 " + " ".join(f"{v:.3f}" for v in data.dat_quantiles)
          + " | ours " + " ".join(f"{v:.3f}" for v in ours_q))
    if args.rooms:
        print(f"\n{'room':>5s} {'area':>8s} {'MM9':>6s} {'ours':>6s} {'ratio':>5s} {'floor':>6s}  (MM9 polygons by nearest face)")
        for room in sorted(set(data.face_sector.tolist())):
            mask = data.sector == room
            ours = data.mean(lit, mask)
            entry = data.dat_rooms.get(room)
            mm9 = entry[0] / entry[1] if entry else None
            area = data.weight[mask].sum()
            fl = data.sector_floor[room] if room not in levels else floor_of(levels[room])
            mm9_text = f"{mm9 @ LUMA:6.3f} {ours @ LUMA / max(mm9 @ LUMA, 1e-6):5.2f}" if mm9 is not None else "     -     -"
            print(f"{room:5d} {area:8.0f} {mm9_text[:6]} {ours @ LUMA:6.3f} {mm9_text[7:]} {fl * a:6.3f}")
    return 0


def grid(data, b, sb, top, levels, skip) -> int:
    """Nelder-Mead over (direct, ambient[, sky]) from a few starts, on up to 40 000 texels a zone drawn by weight."""
    from scipy.optimize import minimize
    rng = np.random.default_rng(1)
    floor = data.sector_floor[data.sector].copy()
    for sec, level in levels.items():
        floor[data.sector == sec] = floor_of(level)
    S = data.terms["sky_direct"] + sb * data.terms["sky_indirect"] if data.has_sky else None
    floor = floor[:, None] * data.colour
    zones = {}
    for name in data.zones:
        mask = data.zone_mask[name]
        if name in skip or not mask.any() or not data.dat[name][0]:
            continue
        idx = np.flatnonzero(mask)
        w = data.weight[idx]
        pick = rng.choice(idx, size=min(40000, len(idx)), p=w / w.sum())
        zones[name] = (data.terms["direct"][pick], data.terms["indirect"][pick], floor[pick],
                       S[pick] if S is not None else None, hvl.stats(data.dat[name])["mean"])

    pick = rng.choice(len(data.weight), size=min(200000, len(data.weight)), p=data.weight / data.weight.sum())
    G = (data.terms["direct"][pick], data.terms["indirect"][pick], floor[pick], S[pick] if S is not None else None)

    def error(x, report=False):
        d, a = x[0], x[1]
        s = x[2] if S is not None else 0.0
        if min(d, a, s) < 0:
            return 1e9
        err, info = 0.0, []
        for name, (D, I, F, SS, target) in zones.items():
            lit = d * D + d * b * I + a * F
            if SS is not None:
                lit = lit + s * SS
            mean = np.minimum(lit, top).mean(0)
            lum = np.log(mean @ LUMA / (target @ LUMA))
            br = np.log(mean[2] / mean[0] / (target[2] / target[0]))
            gr = np.log(mean[1] / mean[0] / (target[1] / target[0]))
            err += lum ** 2 + 0.5 * (br ** 2 + gr ** 2)
            info.append(f"{name} {np.exp(lum):.2f}")
        lit = x[0] * G[0] + x[0] * b * G[1] + x[1] * G[2]
        if G[3] is not None:
            lit = lit + s * G[3]
        q = np.quantile(np.minimum(lit, top) @ LUMA, QUANTILES)
        spread = float((np.log(np.maximum(q, 1e-4) / np.maximum(data.dat_quantiles, 1e-4)) ** 2).sum())
        info.append("p10/50/90 " + "/".join(f"{v:.2f}" for v in q / np.maximum(data.dat_quantiles, 1e-4)))
        err = err / len(zones) + CONTRAST * spread
        return (err, ", ".join(info)) if report else err

    results = []
    for start in ((0.5, 0.3, 0.3), (1.0, 0.6, 0.6), (0.3, 0.1, 0.1), (0.8, 1.0, 0.2)):
        x0 = start if S is not None else start[:2]
        res = minimize(error, x0, method="Nelder-Mead", options={"xatol": 0.005, "fatol": 1e-5, "maxiter": 400})
        results.append((res.fun, tuple(res.x)))
    for fun, x in sorted(results)[:2]:
        err, info = error(x, True)
        print(f"err {err:.4f} direct {x[0]:.3f} ambient {x[1]:.3f}" + (f" sky {x[2]:.3f}" if S is not None else "")
              + f": {info}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
