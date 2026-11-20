#!/usr/bin/env python3
"""brightscale_lightmaps.py <MAP>.dat: per isolated Light: MM9's lightmap rise over the polygon's ambient floor, divided by colour x N.L x falloff, at
texels only this light reaches (no other Light within its radius, faces turned away from any StaticSunLight), not
saturated. If the preprocessor applies BrightScale, this gain k follows BrightScale; if not, k does not."""
import sys, re
from pathlib import Path
import numpy as np
ROOT = Path("/home/pjasicek/github/OpenYAMM")
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
from transcode_mm9_dat_to_odm import read_dat_world
from lightmap_transfer import DatLightmaps
from dungeon.geometry import sample_polygon

world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS" / sys.argv[1])
m = re.search(r"ambientlight\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", world.world_info.properties, re.I)
amb = np.array([float(v) for v in m.groups()]) if m else np.zeros(3)
lm = DatLightmaps(world)
lights, sun = [], None
for o in world.objects:
    p = {q.name: q.value for q in o.properties}
    if o.name == "StaticSunLight":
        pitch, yaw = (float(v) for v in p["Rotation"][:2])
        sun = -np.array([np.sin(yaw) * np.cos(pitch), -np.sin(pitch), np.cos(yaw) * np.cos(pitch)])
    if o.name in ("Light", "DirLight"):
        lights.append((np.array(p["Pos"], float), float(p.get("LightRadius", 300)),
                       np.array(p.get("LightColor", p.get("InnerColor", [255]*3)), float), float(p.get("BrightScale", 1.0)), o.name))
P = np.array([l[0] for l in lights]); R = np.array([l[1] for l in lights])
results = []
for li, (pos, r, col, bs, cls) in enumerate(lights):
    if cls != "Light":
        continue
    ch = int(np.argmax(col))
    if col[ch] < 100:
        continue
    ks = []
    for poly in lm.polys:
        dplane = float(poly["n"] @ pos - poly["d"])
        if dplane <= 2 or dplane > r:
            continue
        if sun is not None and poly["n"] @ sun > -0.05:
            continue
        ring = poly["ring"]
        if np.min(np.linalg.norm(ring - pos, axis=1)) > r + 1e4:
            continue
        pts = sample_polygon(ring, 24)
        delta = pos - pts; dist = np.linalg.norm(delta, axis=1)
        keep = (dist < 0.7 * r) & (dist > 0.1 * r)
        if not keep.any():
            continue
        pts, delta, dist = pts[keep], delta[keep], dist[keep]
        others = np.linalg.norm(P[None] - pts[:, None], axis=2) < R[None] + 8
        others[:, li] = False
        alone = ~others.any(1)
        if not alone.any():
            continue
        pts, delta, dist = pts[alone], delta[alone], dist[alone]
        ndl = (delta @ poly["n"]) / dist


        # MM9 lightmap texel under each point (the polygon's own frame, lightmap_transfer.DatLightmaps)
        rgb, grid = poly["rgb"], poly["g"]
        h, w = rgb.shape[:2]
        rel = pts - poly["o"]
        x = np.clip(np.round((w - 1) - (rel @ poly["p"]) / grid), 0, w - 1).astype(int)
        y = np.clip(np.round((rel @ poly["q"]) / grid), 0, h - 1).astype(int)
        v = rgb[y, x, ch]
        ok = (ndl > 0.3) & (v < 245)
        if not ok.any():
            continue
        rise = v[ok] - amb[ch]
        for model in ("lin",):
            f = (1 - dist[ok] / r)
        ks.extend((rise / (col[ch] * ndl[ok] * f)).tolist())
    if len(ks) >= 8:
        results.append((bs, float(np.median(ks)), len(ks), r))
results = np.array(results)
print(sys.argv[1], "isolated lights", len(results), "ambient", amb[0])
if len(results):
    for b in sorted(set(np.round(results[:, 0], 2))):
        sel = np.round(results[:, 0], 2) == b
        print("  BrightScale %.2f: %3d lights, median gain k %.2f (quartiles %.2f-%.2f)" % (
            b, sel.sum(), np.median(results[sel, 1]), np.percentile(results[sel, 1], 25), np.percentile(results[sel, 1], 75)))
    if len(set(results[:, 0])) > 1:
        print("  correlation(BrightScale, k) %.2f" % np.corrcoef(results[:, 0], results[:, 1])[0, 1])
