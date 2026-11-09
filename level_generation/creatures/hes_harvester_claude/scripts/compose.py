#!/usr/bin/env python3
"""Step 4 (after hes_turrets_claude/scripts/compose.py): the Harvester's runtime textures from its Meshy retexture
(meshy/harvester_retexture_v1/), one 2048x2048 atlas (xatlas, prepare_uv.py).

- Base colour: Meshy's, every island dilated 8 texels into its gutter.
- The pieces build_actor.py adds have their own small material (HS_Glow_Harvester): a 128x128 swatch map of 64x64
  quadrants, `nozzle` (the slag sprayer's throat: a radial white-yellow to orange disc), `grille` (the heat vents'
  louvres: orange-red bars on near-black), `core` (the core drums' slots: white-gold, a brighter centre line), and an
  emission map (the swatches; the base colour is them x GLOW_BASE). The xatlas layout has no free
  square for swatches (its gutters are about 4 texels).
- Normal: Meshy's, measured with tools/normal_map_convention.measure and converted to glTF (+y up) when needed.
- Metal/roughness (glTF ORM, R = 1): metallic binarised (Meshy >= 0.5 -> 0.85, the builder's gold; else 0),
  roughness Meshy's, at least 0.45 on non-metal (Meshy's glazed ceramic read like plastic).
Writes textures/harvester_{basecolor (2048), normal (1024), orm (1024), seam_mask (1024), glow_basecolor, glow_emissive,
glow_mask (128)}.png and
textures/harvester_swatches.json (the swatch UV rectangles [u0, v0, u1, v1] in the glow map)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / 'scripts'))
sys.path.insert(0, str(REPO / 'tools'))
from raster import dilate, rasterise  # noqa: E402
import normal_map_convention  # noqa: E402

RES = 2048
SRC = HERE / 'meshy' / 'harvester_retexture_v1'
OUT = HERE / 'textures'
OUT.mkdir(exist_ok=True)


def load(kind):
    return np.array(Image.open(SRC / f'texture_urls_0_{kind}.png').convert('RGB').resize((RES, RES), Image.LANCZOS)
                    ).astype(np.float32) / 255.0


d = np.load(HERE / 'work' / 'harvester_tris.npz')
tri, pos = rasterise(d['uv'], d['co'], d['n'], RES)
covered = tri >= 0
base, metal, rough, nrm = load('base_color'), load('metallic'), load('roughness'), load('normal')


# ---------------------------------------------------------------- finish (integrator review, 2026-10-23)
# Meshy painted the ivory plates with brown rust blotches and the resin cables brown; the sheet is clean ivory plate
# with gold trim and dark violet-black resin. Pieces (connected components of the retexture mesh, by shared
# positions) are classed by their texels: IVORY_SHARE of ivory-like texels (light, low saturation) makes a plate, repainted IVORY with only its fine detail (luminance over a 3-texel blur) and a soft large-scale shade; the
# drill, the boom and the tracks are dark steel; a piece mostly metal is gold; every other piece is resin, repainted
# RESIN with its relative brightness. Metal texels (gold trim, pivots, buckets) go through one aged-gold ramp by luminance; on the
# plates only the bright gold stays metal (Meshy's metallic map also covers the rust there).
IVORY = np.array([0.93, 0.85, 0.67])                  # the sheet's warm cream plate
GOLD_DARK, GOLD_LIGHT = np.array([0.26, 0.16, 0.06]), np.array([0.80, 0.60, 0.27])
RESIN = np.array([0.15, 0.085, 0.19])
STEEL = np.array([0.21, 0.20, 0.21])
IVORY_SHARE = 0.18


def blur(img, mask, sigma):
    """Masked Gaussian blur (normalised convolution) of a 2D map over the covered texels."""
    from scipy.ndimage import gaussian_filter
    w = gaussian_filter(mask.astype(np.float32), sigma)
    return gaussian_filter(np.where(mask, img, 0).astype(np.float32), sigma) / np.maximum(w, 1e-4)


tri_pos = d['co'].reshape(-1, 3).round(4)
_, vid = np.unique(tri_pos, axis=0, return_inverse=True)
vid = vid.reshape(-1, 3)
parent = np.arange(vid.max() + 1)


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for a, b, c in vid:
    ra, rb, rc = find(a), find(b), find(c)
    parent[rb] = ra; parent[find(rc)] = ra
comp_of_tri = np.array([find(t[0]) for t in vid])
_, comp_of_tri = np.unique(comp_of_tri, return_inverse=True)
comp = np.where(covered, comp_of_tri[np.maximum(tri, 0)], -1)
lum = base @ np.array([0.2126, 0.7152, 0.0722])
sat = (base.max(-1) - base.min(-1)) / np.maximum(base.max(-1), 1e-4)
is_metal = metal[..., 0] >= 0.5
nonmetal = covered & ~is_metal
ivory_like = nonmetal & (lum > 0.5) & (sat < 0.5)
ncomp = comp_of_tri.max() + 1
share = (np.bincount(comp[ivory_like], minlength=ncomp) / np.maximum(np.bincount(comp[nonmetal], minlength=ncomp), 1))
centre = np.array([d['co'][comp_of_tri == k].reshape(-1, 3).mean(0) for k in range(ncomp)])
tri_part = d['part']
steel_comp = np.array([np.isin(tri_part[comp_of_tri == k], (1, 2)).mean() > 0.5 for k in range(ncomp)])
steel_comp |= (np.abs(centre[:, 0]) > 1.05) & (centre[:, 2] < 1.0) & (share < IVORY_SHARE)   # the tracks
plate_comp = (share >= IVORY_SHARE) & ~steel_comp
metal_share = np.bincount(comp[covered & is_metal], minlength=ncomp) / np.maximum(np.bincount(comp[covered], minlength=ncomp), 1)
gold_comp = (metal_share > 0.5) & ~plate_comp & ~steel_comp
kind = np.where(covered, np.select([plate_comp[np.maximum(comp, 0)], steel_comp[np.maximum(comp, 0)],
                                    gold_comp[np.maximum(comp, 0)]], [1, 2, 4], 3), 0)
fine = np.clip(lum / np.maximum(blur(lum, covered, 3), 1e-3), 0.8, 1.15)
large = np.clip(blur(lum, covered, 24) / np.maximum(np.median(lum[ivory_like]), 1e-3), 0.0, 1.0) ** 0.25
rel = np.clip(lum / np.maximum(blur(lum, covered, 40), 1e-3), 0.55, 1.8)
# Meshy's metallic map also marks the rust streaks on the plates (the plates have no crisp trim to keep): ivory
hue = np.degrees(np.arctan2(np.sqrt(3) * (base[..., 1] - base[..., 2]),
                            2 * base[..., 0] - base[..., 1] - base[..., 2])) % 360
rust = covered & is_metal & (kind == 1)
# and on the resin pieces (mostly non-metal: cables, resin mass) its "metal" spots are grime: resin there; on the
# tracks the dark "metal" is grime too; mostly-metal pieces (gold rings, buckets, pivots) stay gold
rust |= covered & is_metal & ((kind == 3) | ((kind == 2) & (lum < 0.3)))
is_metal &= ~rust
metal[rust] = 0.0
nonmetal = covered & ~is_metal
gold = covered & is_metal
base[gold] = (GOLD_DARK + (GOLD_LIGHT - GOLD_DARK) * np.clip(lum / 0.6, 0, 1)[..., None] ** 0.8)[gold]
plate = nonmetal & (kind == 1); steel = nonmetal & (kind == 2); resin = nonmetal & (kind == 3)
base[plate] = (IVORY * (fine * np.clip(large, 0.82, 1.0))[..., None])[plate]
base[steel] = (STEEL * rel[..., None])[steel]
base[resin] = (RESIN * rel[..., None])[resin]
print('finish: pieces', ncomp, 'plates', int(plate_comp.sum()), 'steel', int(steel_comp.sum()),
      'gold pieces', int(gold_comp.sum()), 'texels plate/steel/resin/gold/rust', int(plate.sum()), int(steel.sum()), int(resin.sum()), int(gold.sum()),
      int(rust.sum()))

S = 64
GLOW_BASE = 0.25
yy, xx = np.mgrid[0:S, 0:S]
u = (xx + 0.5) / S; v = (yy + 0.5) / S
r = np.hypot(u - 0.5, v - 0.5) / 0.5
paint = {}
core, rim = np.array([1.0, 0.72, 0.28]), np.array([0.95, 0.26, 0.04])
paint['nozzle'] = core + (rim - core) * np.clip(r, 0, 1)[..., None] ** 1.2
# the vent grille: eight hot orange-red bars (hottest along the middle of the opening) between thin dark slats
slat = (v * 8) % 1.0 > 0.82
hot = np.exp(-((u - 0.5) / 0.45) ** 2) * np.exp(-((v - 0.5) / 0.6) ** 2)
bar = np.array([0.92, 0.22, 0.04]) + (np.array([1.0, 0.62, 0.20]) - np.array([0.92, 0.22, 0.04])) * hot[..., None]
paint['grille'] = np.where(slat[..., None], np.array([0.05, 0.02, 0.015]), bar)
glow = np.exp(-((u - 0.5) / 0.22) ** 2)
paint['core'] = np.array([1.0, 0.86, 0.52]) + (np.array([1.0, 0.98, 0.9]) - np.array([1.0, 0.86, 0.52])) * glow[..., None]
swatch = {}
glow_base = np.zeros((2 * S, 2 * S, 3)); glow_mask = np.zeros((2 * S, 2 * S))
for k, (name, img) in enumerate(paint.items()):
    x, y = (k % 2) * S, (k // 2) * S
    glow_base[y:y + S, x:x + S] = img
    glow_mask[y:y + S, x:x + S] = img @ np.array([0.2126, 0.7152, 0.0722])
    m = 4 / (2 * S)                                       # keep 4 texels clear of the quadrant edge (mip bleed)
    swatch[name] = [x / (2 * S) + m, 1 - (y + S) / (2 * S) + m, (x + S) / (2 * S) - m, 1 - y / (2 * S) - m]
# the glow comes from the emission: the lit base colour is the swatch darkened (a bright lit base under the emission
# washed the orange out to peach)
Image.fromarray((np.clip(glow_base * GLOW_BASE, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'harvester_glow_basecolor.png')
Image.fromarray((np.clip(glow_base, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'harvester_glow_emissive.png')
Image.fromarray((np.clip(glow_mask, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'harvester_glow_mask.png')
json.dump(swatch, open(OUT / 'harvester_swatches.json', 'w'), indent=1)

base = dilate(base, covered, 8); metal = dilate(metal, covered, 8)
rough = dilate(rough, covered, 8); nrm = dilate(nrm, covered, 8)
metallic = np.where(metal[..., 0] >= 0.5, 0.85, 0.0)
roughness = np.where(metallic > 0, rough[..., 0], np.maximum(rough[..., 0], 0.45))
orm = np.stack([np.ones_like(roughness), roughness, metallic], -1)
correlation = normal_map_convention.measure((nrm * 255).astype(np.uint8))
if correlation <= -0.15:
    nrm[..., 1] = 1.0 - nrm[..., 1]
print('normal correlation', round(float(correlation), 3), 'flipped' if correlation <= -0.15 else 'kept')


def save(img, size, kind):
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    im.resize(size, Image.LANCZOS).save(OUT / f'harvester_{kind}.png')


save(base, (2048, 2048), 'basecolor'); save(nrm, (1024, 1024), 'normal'); save(orm, (1024, 1024), 'orm')

# Orange seams (the sheet's glowing joints): resin texels within SEAM_WIDTH of a plate on the upper hull, broken
# into segments by a smooth 3D pattern so only some joints glow. An emission mask for the hull material
# (claude_shared/emission.py --mask, orange factor); written at 1024.
SEAM_WIDTH = 0.12                                       # plates overlap the cables: a narrower band hides under them
from scipy.spatial import cKDTree  # noqa: E402
plate_pts = pos[plate][::3]
cand = resin & (pos[..., 2] > 1.15) & (pos[..., 2] < 3.0)
dist, _ = cKDTree(plate_pts).query(pos[cand], distance_upper_bound=SEAM_WIDTH * 2)
seam_w = np.zeros(cand.sum(), np.float32)
near = np.isfinite(dist)
seam_w[near] = np.clip(1.0 - dist[near] / SEAM_WIDTH, 0, 1)
pc = pos[cand]
pattern = np.sin(pc[:, 1] * 2.1 + 0.7) * np.sin(pc[:, 0] * 3.3 + pc[:, 2] * 1.7)
seam_w *= (pattern > 0.15)
seam = np.zeros((RES, RES), np.float32)
seam[cand] = seam_w
seam = np.maximum(seam, blur(seam, covered, 1.2) * 0.8)
seam = dilate(seam[..., None].repeat(3, -1), covered, 4)[..., 0]
Image.fromarray((np.clip(seam, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
    OUT / 'harvester_seam_mask.png')
print('seams: texels', int((seam > 0.3).sum()), 'of resin', int(resin.sum()))
print('COMPOSED swatches', swatch, 'coverage', round(float((tri >= 0).mean()), 3))
