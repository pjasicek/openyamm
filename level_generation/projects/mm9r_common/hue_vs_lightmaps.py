#!/usr/bin/env python3
"""
Hue of our baked lighting against MM9's own DAT lightmaps, per zone (read only: nothing is written or rebaked).

    python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_chasmofthedead
    python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_beethoven

The project directory supplies `overrides.yml` (map stem, offset) and the zones: `hue_zones.py` (ZONES) or, failing
that, `dat_lightmaps.py` (ZONES). A zone is a box in MM9's own units, (x0, y0, z0, x1, y1, z1) with y up.

Frame (the converter's, DUNGEON_PLAYBOOK): native = (LT.x, LT.z, LT.y) * 2.56 - offset. The native side takes the
bake's scene (`output/mm9_rework/bakes/<stem>/scene.json`, native face points) and the sidecar in the review root
(`<map>.lighting`, devdocs/INDOOR_BAKED_LIGHTING.md). A native face belongs to a zone when its centre, converted back to
MM9 units, lies in the box; a DAT polygon when its centre does. Texels are weighted by the polygon's or face's area per
texel, so a coarse and a fine lightmap count by surface and not by sample count.

Scale: MM9 texels are bytes (255 = x1, clipped); ours are linear multipliers up to 4 (HDR, the shader clamps the sum to
2). Only ratios are compared. Per zone and source: mean R, G, B, the ratios of the means B/R and G/R, the
brightness-weighted saturation (weight = luminance, saturation = (max - min) / max per texel), the 90th percentile
and the mean over the brightest 5 % (the hot pools) of the per-texel B/R and G/R over the lit texels (luminance of at least half the zone mean, so the 8-bit dark noise of
MM9 does not decide it).

Chroma factor of a zone = |ln(B/R), ln(G/R)| of ours over MM9's; > 1 means ours is more coloured. The suggested map
multiplier is the median over zones whose MM9 chroma is clearly non-neutral, as a factor on the light colours' distance
from white.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722])


def load_zones(project: Path) -> dict:
    for name in ("hue_zones.py", "dat_lightmaps.py"):
        path = project / name
        if path.exists():
            spec = importlib.util.spec_from_file_location("zones_" + path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.ZONES
    raise SystemExit(f"{project}: no hue_zones.py or dat_lightmaps.py with ZONES")


def read_pages_and_faces(path: Path):
    data = path.read_bytes()
    magic, version, header, _hash, face_count, _sectors, page_count, _deps, page_off, face_off = \
        struct.unpack_from("<8sIIQ6I", data, 0)[:10]
    assert magic == b"OYILIT1\0", magic
    pages = []
    for i in range(page_count):
        width, height, offset, size = struct.unpack_from("<4I", data, page_off + 16 * i)
        payload = np.frombuffer(data, np.uint8, size, offset)
        out = np.empty((width * height, 4), np.uint8)
        pos = filled = 0
        while pos < size:
            tag = int(payload[pos])
            count = (tag & 127) + 1
            if tag & 128:
                out[filled:filled + count] = payload[pos + 1:pos + 5]
                pos += 5
            else:
                out[filled:filled + count] = payload[pos + 1:pos + 1 + 4 * count].reshape(count, 4)
                pos += 1 + 4 * count
            filled += count
        assert filled == width * height and pos == size
        # BGRM bytes -> linear RGB: (c / 255) * (M / 255) * 4
        rgb = out[:, [2, 1, 0]].astype(np.float32) / 255 * (out[:, 3:4].astype(np.float32) / 255) * 4
        pages.append(rgb.reshape(height, width, 3))
    faces = []
    for i in range(face_count):
        page, flags, *axes = struct.unpack_from("<HH8f", data, face_off + 36 * i)
        faces.append(None if page == 0xFFFF else (page, np.array(axes[:4]), np.array(axes[4:])))
    return pages, faces


def polygon_area(points: np.ndarray) -> float:
    total = np.zeros(3)
    for i in range(len(points)):
        total += np.cross(points[i], points[(i + 1) % len(points)])
    return float(np.linalg.norm(total) / 2)


def native_texels(scene: dict, pages, faces, offset, zones: dict):
    """Per zone: (rgb texels, weights) of the native lightmaps. Weight = face area (LT^2) / texel count."""
    off = np.array(offset, float)
    out = {name: ([], []) for name in zones}
    boxes = {n: (np.array(b[:3], float), np.array(b[3:], float)) for n, b in zones.items()}
    centres = []
    for face in scene["faces"]:
        record = faces[face["index"]]
        if record is None or not face["visible"]:
            continue
        pts = np.array(face["points"], float)
        centre = pts.mean(0)
        lt = np.array([centre[0] + off[0], centre[2] + off[2], centre[1] + off[1]]) / SCALE
        page, ua, va = record
        rgb_page = pages[page]
        height, width = rgb_page.shape[:2]
        hom = np.c_[pts, np.ones(len(pts))]
        uv = np.stack([hom @ ua, hom @ va], 1) * [width, height]
        x0, y0 = np.floor(uv.min(0)).astype(int)
        x1, y1 = np.ceil(uv.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        grid = np.stack([xs.ravel(), ys.ravel()], 1)
        inside = np.ones(len(grid), bool)
        signs = []
        for i in range(len(uv)):
            a, b = uv[i], uv[(i + 1) % len(uv)]
            signs.append((b[0] - a[0]) * (grid[:, 1] - a[1]) - (b[1] - a[1]) * (grid[:, 0] - a[0]))
        signs = np.array(signs)
        inside = (signs >= -1e-6).all(0) | (signs <= 1e-6).all(0)
        cells = grid[inside].astype(int)
        if not len(cells):
            cells = np.array([[int(uv[:, 0].mean()), int(uv[:, 1].mean())]])
        cells[:, 0] = np.clip(cells[:, 0], 0, width - 1)
        cells[:, 1] = np.clip(cells[:, 1], 0, height - 1)
        texels = rgb_page[cells[:, 1], cells[:, 0]]
        weight = polygon_area(pts) / SCALE ** 2 / len(texels)
        centres.append((lt, texels.mean(0)))
        for name, (low, high) in boxes.items():
            if (lt >= low).all() and (lt <= high).all():
                out[name][0].append(texels)
                out[name][1].append(np.full(len(texels), weight))
    return out, centres


def dat_texels(world, zones: dict):
    model = next(m for m in world.world_models if m.name == "PhysicsBSP")
    out = {name: ([], []) for name in zones}
    boxes = {n: (np.array(b[:3], float), np.array(b[3:], float)) for n, b in zones.items()}
    centres = []
    for poly in model.polies:
        pixels = getattr(poly, "lightmap_pixels_bgra", None)
        if not pixels:
            continue
        value = np.array(pixels, np.int64)
        texels = np.stack([(value >> 16) & 255, (value >> 8) & 255, value & 255], 1).astype(float) / 255
        pts = np.array([model.points[d.vertex_index] for d in poly.disk_verts], float)
        weight = polygon_area(pts) / len(texels) if len(pts) >= 3 else 1.0
        centre = np.array(poly.center, float)
        centres.append((centre, texels.mean(0)))
        for name, (low, high) in boxes.items():
            if (centre >= low).all() and (centre <= high).all():
                out[name][0].append(texels)
                out[name][1].append(np.full(len(texels), weight))
    return out, centres


def wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    cum = np.cumsum(weights[order])
    return float(values[order][np.searchsorted(cum, q * cum[-1])])


def stats(parts) -> dict | None:
    if not parts[0]:
        return None
    rgb = np.concatenate(parts[0])
    w = np.concatenate(parts[1])
    mean = (rgb * w[:, None]).sum(0) / w.sum()
    lum = rgb @ LUMA
    big = rgb.max(1)
    sat = np.where(big > 0, (big - rgb.min(1)) / np.maximum(big, 1e-9), 0)
    lw = w * lum
    lit = (lum >= 0.5 * float((lum * w).sum() / w.sum())) & (rgb[:, 0] > 0)
    br = rgb[lit, 2] / rgb[lit, 0]
    gr = rgb[lit, 1] / rgb[lit, 0]
    lw_lit = w[lit]
    cut = wquantile(lum, w, 0.95)
    top = lum >= cut
    top_mean = (rgb[top] * w[top, None]).sum(0) / w[top].sum()
    return {"top_b_r": top_mean[2] / max(top_mean[0], 1e-9), "top_g_r": top_mean[1] / max(top_mean[0], 1e-9),
            "mean": mean, "b_r": mean[2] / mean[0], "g_r": mean[1] / mean[0],
            "sat": float((lw * sat).sum() / lw.sum()) if lw.sum() > 0 else 0.0,
            "p90_b_r": wquantile(br, lw_lit, 0.9) if lit.any() else float("nan"),
            "p90_g_r": wquantile(gr, lw_lit, 0.9) if lit.any() else float("nan"),
            "texels": len(rgb), "area": float(w.sum())}


def chroma(s: dict) -> float:
    return math.hypot(math.log(max(s["b_r"], 1e-6)), math.log(max(s["g_r"], 1e-6)))


def verdict(dat: dict, nat: dict) -> tuple[str, float]:
    cd, cn = chroma(dat), chroma(nat)
    if cd < 0.08:
        return (f"MM9 neutral (chroma {cd:.2f}); ours {cn:.2f}: " + ("matches" if cn < 0.12 else "too coloured"), float("nan"))
    factor = cn / cd
    # direction: angle between the log-ratio vectors
    vd = np.array([math.log(dat["b_r"]), math.log(dat["g_r"])])
    vn = np.array([math.log(nat["b_r"]), math.log(nat["g_r"])])
    angle = math.degrees(math.acos(np.clip(vd @ vn / (np.linalg.norm(vd) * np.linalg.norm(vn) + 1e-12), -1, 1)))
    note = f", hue off by {angle:.0f} deg" if angle > 25 else ""
    if factor > 1.25:
        return f"too saturated, x{factor:.2f}{note}", factor
    if factor < 0.8:
        return f"too neutral, x{factor:.2f}{note}", factor
    return f"matches (x{factor:.2f}){note}", factor


def check_vertices(world, scene: dict, offset) -> None:
    """The frame itself: every DAT vertex should have a native vertex at the converted position (rounding only)."""
    from scipy.spatial import cKDTree
    model = next(m for m in world.world_models if m.name == "PhysicsBSP")
    native = np.array([p for f in scene["faces"] for p in f["points"]], float) + np.array(offset, float)
    as_lt = np.c_[native[:, 0], native[:, 2], native[:, 1]] / SCALE
    dist, _ = cKDTree(as_lt).query(np.array(model.points, float)[::5])
    print(f"Frame check (vertices): {len(dist)} DAT vertices -> nearest native vertex converted back to MM9 units: "
          f"median {np.median(dist):.2f}, 90th pct {np.percentile(dist, 90):.2f}, {100 * (dist < 2).mean():.1f}% within 2")


def check_frame(dat_centres, nat_centres) -> None:
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(1)
    nat = np.array([c[0] for c in nat_centres])
    nat_lum = np.array([c[1] @ LUMA for c in nat_centres])
    tree = cKDTree(nat)
    pick = rng.choice(len(dat_centres), min(600, len(dat_centres)), replace=False)
    pts = np.array([dat_centres[i][0] for i in pick])
    dist, idx = tree.query(pts)
    dat_lum = np.array([dat_centres[i][1] @ LUMA for i in pick])
    ok = dist < 48
    corr = np.corrcoef(np.log(dat_lum[ok] + 0.01), np.log(nat_lum[idx[ok]] + 0.01))[0, 1] if ok.sum() > 3 else float("nan")
    print(f"Centre check (merged faces shift centres): {len(pick)} DAT polygon centres -> nearest native face centre (LT units): median "
          f"{np.median(dist):.1f}, 90th pct {np.percentile(dist, 90):.1f}, {100 * ok.mean():.0f}% within 48; "
          f"log-luminance correlation DAT vs ours on those pairs {corr:.2f}")
    print(f"  extents LT  DAT x {min(c[0][0] for c in dat_centres):.0f}..{max(c[0][0] for c in dat_centres):.0f}"
          f" y {min(c[0][1] for c in dat_centres):.0f}..{max(c[0][1] for c in dat_centres):.0f}"
          f" z {min(c[0][2] for c in dat_centres):.0f}..{max(c[0][2] for c in dat_centres):.0f};"
          f" native-as-LT x {nat[:, 0].min():.0f}..{nat[:, 0].max():.0f} y {nat[:, 1].min():.0f}..{nat[:, 1].max():.0f}"
          f" z {nat[:, 2].min():.0f}..{nat[:, 2].max():.0f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--root", type=Path, default=ROOT / "output/mm9_rework/assets_dev", help="review root")
    ap.add_argument("--scene", type=Path, help="bake scene.json (default output/mm9_rework/bakes/<stem>/scene.json)")
    ap.add_argument("--json", type=Path, help="also write the numbers here")
    args = ap.parse_args()
    project = args.project.resolve()
    settings = yaml.safe_load((project / "overrides.yml").read_text())["map"]
    stem, offset = settings["stem"], settings.get("offset", (0, 0, 0))
    zones = load_zones(project)
    scene = json.loads((args.scene or ROOT / f"output/mm9_rework/bakes/{stem}/scene.json").read_text())
    pages, faces = read_pages_and_faces(args.root / f"worlds/mm9/maps/{stem}.lighting")
    assert len(faces) == scene["face_count"], "scene.json is not the bake's scene (face count differs)"
    world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS" / settings.get("dat", f"{stem.upper()}.dat"))
    dat, dat_centres = dat_texels(world, zones)
    nat, nat_centres = native_texels(scene, pages, faces, offset, zones)
    print(f"{stem}: scale {SCALE}, offset {tuple(offset)}; native = (LT.x, LT.z, LT.y) * scale - offset")
    check_vertices(world, scene, offset)
    check_frame(dat_centres, nat_centres)
    print("MM9 texels are bytes/255 (clipped at x1); ours are linear multipliers (HDR). Ratios compare directly.\n")
    head = (f"{'zone':16s} {'src':4s} {'R':>6s} {'G':>6s} {'B':>6s} {'B/R':>5s} {'G/R':>5s} {'sat':>5s} "
            f"{'p90B/R':>6s} {'p90G/R':>6s} {'top5B/R':>7s} {'top5G/R':>7s} {'area':>9s}")
    print(head)
    results, factors = {}, []
    for name in zones:
        d, n = stats(dat[name]), stats(nat[name])
        if d is None or n is None:
            print(f"{name:16s} no data (MM9 {d is not None}, ours {n is not None})")
            continue
        for tag, s in (("MM9", d), ("ours", n)):
            print(f"{name:16s} {tag:4s} {s['mean'][0]:6.3f} {s['mean'][1]:6.3f} {s['mean'][2]:6.3f} {s['b_r']:5.2f} "
                  f"{s['g_r']:5.2f} {s['sat']:5.2f} {s['p90_b_r']:6.2f} {s['p90_g_r']:6.2f} {s['top_b_r']:7.2f} {s['top_g_r']:7.2f} {s['area']:9.0f}")
        text, factor = verdict(d, n)
        hot = ""
        if d["p90_b_r"] > 0 and d["p90_g_r"] > 0:
            hot = (f"; p90 ours/MM9 B/R x{n['p90_b_r'] / d['p90_b_r']:.2f} G/R x{n['p90_g_r'] / d['p90_g_r']:.2f}, "
                   f"saturation x{n['sat'] / max(d['sat'], 1e-6):.2f}")
        print(f"{'':16s} -> {text}{hot}")
        results[name] = {"mm9": {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in d.items()},
                         "ours": {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in n.items()},
                         "verdict": text, "chroma_factor": factor}
        if chroma(d) >= 0.15 and not math.isnan(factor):
            factors.append((factor, d["sat"] / max(n["sat"], 1e-6)))
    if factors:
        print(f"\nSuggested light-colour multiplier (distance from white), median over {len(factors)} coloured zones: "
              f"x{1 / float(np.median([f[0] for f in factors])):.2f} by log-ratio chroma, "
              f"x{float(np.median([f[1] for f in factors])):.2f} by weighted saturation (not applied)")
    if args.json:
        args.json.write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
