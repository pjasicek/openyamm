"""Re-render the designed sari tile on the texture-pass layout (followup-mfp, 2026-11-11).

The approved sari is not paint: mm6_mfp_codex/scripts/round2_textures.py maps references_hd/round2_sari_tile.png onto
the skirt (piece 1: elliptic-cylinder repeat, 8 around, 12 cm high) and the diagonal sash (piece 6: planar repeat,
11.5 cm) from the bind-pose surface position, then baked it at 4096. This script evaluates the same mapping at every
texel of the new 2048 layout, 4x4 supersampled inside each texel (anti-aliased, no resampling of the old bake), so
the sari is as crisp as the tile allows at the new density.

Pieces come from the production round-2 mesh (work/round2/mesh0.npz, Blender Z-up; installed glTF Y-up maps as
(x, -z, y)); a texel takes the piece of the nearest round-2 vertex. A texel keeps the render only where it agrees
with the approved colour around it (both blurred to the approved bake's scale), so later edits and piece-boundary
mistakes keep the approved colour.

Usage: mfp_sari.py <layout npz> <approved prefix> <out prefix> [median threshold 12] [debug]
Writes <out>_sari.png (render, padded), <out>_sari_mask.png (255 where used), <out>_sari.json (agreement numbers).
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

import tp_common as C

layout_path, approved, out = sys.argv[1:4]
S = 2048
SS = 4
CODEX = C.CREATURES / 'mm6_mfp_codex'

layout = np.load(layout_path)
before = np.load(C.lod0_path())
r = np.load(f'{approved}_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
ys, xs = np.nonzero(cov)
t = tri_id[cov]
b = bary[cov]
pos, tri = before['pos'], before['tri']
P = (b[:, :, None] * pos[tri[t]]).sum(1)


def to_blender(p):
    return np.stack([p[..., 0], -p[..., 2], p[..., 1]], -1)


# ---- piece per texel from the production mesh
m = np.load(CODEX / 'work/round2/mesh0.npz')
tree = cKDTree(m['co'])
d, ix = tree.query(to_blender(P), workers=4)
piece = m['piece'][ix]
print('nearest round-2 vertex p50/p99 mm', np.percentile(d, [50, 99]) * 1000)

# ---- supersampled positions inside each texel: barycentrics from the layout triangle's UVs
uvp = layout['uv'] * S                                   # (T, 3, 2) pixel coords (x = u S, y = v S)
M = np.stack([uvp[:, 1] - uvp[:, 0], uvp[:, 2] - uvp[:, 0]], -1)   # (T, 2, 2) columns e1, e2
det = np.linalg.det(M)
Minv = np.linalg.inv(np.where(np.abs(det)[:, None, None] < 1e-12, np.eye(2), M))
xyz = layout['xyz']
if not np.allclose(xyz, pos[tri], atol=1e-5):
    print('WARNING layout xyz differs from the installed LOD0 positions; using installed positions')
xyz = pos[tri]

tile = np.asarray(Image.open(CODEX / 'references_hd/round2_sari_tile.png').convert('RGB'), np.float32)
TH, TW = tile.shape[:2]
theta = np.linspace(-np.pi, np.pi, 4097)
ds = np.sqrt((.185 * np.cos(theta)) ** 2 + (.13 * np.sin(theta)) ** 2)
arc = np.r_[0, np.cumsum((ds[1:] + ds[:-1]) * .5 * np.diff(theta))]
arc /= arc[-1]


def tile_uv(q, kind):
    """q (N, 3) Blender positions -> tile uv (N, 2), v up, as round2_textures.py."""
    if kind == 1:
        ang = np.arctan2(q[:, 0] / .185, -(q[:, 1] + .025) / .13)
        u = np.interp(ang, theta, arc) * 8 + .5
        v = (q[:, 2] - .24) / .12 + .5
    else:
        u = (q @ np.array([.85, 0, -.526]) + .62) / .115 + .5
        v = (q @ np.array([.526, 0, .85])) / .115
    return np.stack([u, v], 1)


def sample_tile(img, uv):
    co = np.array([(1 - uv[:, 1] % 1) * TH - .5, (uv[:, 0] % 1) * TW - .5])
    return np.stack([ndimage.map_coordinates(img[:, :, i], co, order=1, mode='grid-wrap') for i in range(3)], 1)


# light pre-blur of the tile (each 4x4 subsample still covers a few tile pixels)
tile_f = np.stack([ndimage.gaussian_filter(tile[:, :, i], 0.7, mode='wrap') for i in range(3)], -1)

offs = (np.arange(SS) + .5) / SS
ox, oy = np.meshgrid(offs, offs)
ox, oy = ox.ravel(), oy.ravel()
appr = np.asarray(Image.open(f'{approved}_basecolor.png').convert('RGB'), np.float32)


def blur(a, s):
    return np.stack([ndimage.gaussian_filter(a[:, :, i], s) for i in range(3)], -1)


SIG = 1.6
appr_b = blur(appr, SIG)
# candidate texels: near a round-2 skirt/sash vertex within 6 cm (both renders are tried on each)
d16, _ = cKDTree(m['co'][np.isin(m['piece'], [1, 6])]).query(to_blender(P), workers=4)
cand = np.flatnonzero(d16 < 0.06)
renders, diffs = {}, {}
for kind in (1, 6):
    acc = np.zeros((len(cand), 3), np.float32)
    tt = t[cand]
    for dx, dy in zip(ox, oy):
        p = np.stack([xs[cand] + dx, ys[cand] + dy], 1) - uvp[tt, 0]
        st = np.einsum('nij,nj->ni', Minv[tt], p)
        w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
        q = to_blender((w[:, :, None] * xyz[tt]).sum(1))
        acc += sample_tile(tile_f, tile_uv(q, kind))
    acc /= len(ox)
    img = appr.copy()
    img[ys[cand], xs[cand]] = acc
    diffs[kind] = np.abs(blur(img, SIG) - appr_b).max(-1)[ys[cand], xs[cand]]
    renders[kind] = acc

# ---- one decision per triangle: the render whose median blurred difference is lower, if it agrees
tc = t[cand]
ntri = len(tri)
score = {}
for kind in (1, 6):
    med = np.full(ntri, np.inf)
    order = np.argsort(tc, kind='stable')
    tcs, ds_ = tc[order], diffs[kind][order]
    starts = np.r_[0, np.flatnonzero(np.diff(tcs)) + 1]
    uniq = tcs[starts]
    for a, b_, u in zip(starts, np.r_[starts[1:], len(tcs)], uniq):
        med[u] = np.median(ds_[a:b_])
    score[kind] = med
choice = np.where(score[1] <= score[6], 1, 6)
best = np.minimum(score[1], score[6])
THR = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != 'debug' else 12.0
# sari pink share of each triangle in the approved colour: the old reduction transfer smeared parts of the sash into
# streaks, which disagree with the clean render; mostly pink triangles take the render within a looser bound
pinkpx = (appr[..., 0] > 150) & (appr[..., 1] < 90) & (appr[..., 2] > 50)
pink = np.bincount(tc, weights=pinkpx[ys[cand], xs[cand]], minlength=ntri) / np.maximum(np.bincount(tc, minlength=ntri), 1)
LOOSE = 45.0
accept = (best < THR) | ((pink >= 0.25) & (best < LOOSE))
pick = choice[tc]
ok = accept[tc]
render = np.where((pick == 1)[:, None], renders[1], renders[6])
dsel = np.where(pick == 1, diffs[1], diffs[6])
# texels inside accepted triangles whose own local difference is large (a later edit) keep the approved colour
loc = np.zeros((S, S), np.float32)
loc[ys[cand], xs[cand]] = dsel
loc = ndimage.maximum_filter(ndimage.median_filter(loc, 5), 3)
ok &= (loc[ys[cand], xs[cand]] < 45) | (pink[tc] >= 0.25)
use = np.zeros((S, S), bool)
use[ys[cand[ok]], xs[cand[ok]]] = True
out_img = appr.copy()
out_img[ys[cand[ok]], xs[cand[ok]]] = render[ok]
area = C.tri_area3(pos[tri])
report = {
    'triangles_skirt': int((accept & (choice == 1)).sum()),
    'triangles_sash': int((accept & (choice == 6)).sum()),
    'area_m2_skirt': float(area[accept & (choice == 1)].sum()),
    'area_m2_sash': float(area[accept & (choice == 6)].sum()),
    'texels_used': int(use.sum()),
    'used_diff_p50_p90_p99': [float(v) for v in np.percentile(dsel[ok], [50, 90, 99])],
    'threshold_median': THR,
    'triangles_by_pink_rule': int(((pink >= 0.25) & (best >= THR) & (best < LOOSE)).sum()),
}
print(json.dumps(report, indent=1))
Image.fromarray(np.clip(np.round(out_img), 0, 255).astype(np.uint8)).save(f'{out}_sari.png')
Image.fromarray((use * 255).astype(np.uint8)).save(f'{out}_sari_mask.png')
open(f'{out}_sari.json', 'w').write(json.dumps(report, indent=1))
if 'debug' in sys.argv[4:]:
    full = appr.copy()
    full[ys[cand], xs[cand]] = render
    Image.fromarray(np.clip(np.round(full), 0, 255).astype(np.uint8)).save(f'{out}_sari_raw.png')
    dd = np.zeros((S, S), np.float32)
    dd[ys[cand], xs[cand]] = dsel
    Image.fromarray(np.clip(dd * 3, 0, 255).astype(np.uint8)).save(f'{out}_sari_diff.png')
if 'diag' in sys.argv[4:]:
    rej = (pink >= 0.25) & ~accept
    print('rejected pink triangles', int(rej.sum()), 'best p10/50/90', np.percentile(best[rej & np.isfinite(best)], [10, 50, 90]),
          'not candidates', int((rej & ~np.isfinite(best)).sum()))
    allpink = np.bincount(t, weights=pinkpx[ys, xs], minlength=ntri) / np.maximum(np.bincount(t, minlength=ntri), 1)
    print('pink triangles overall', int((allpink >= 0.25).sum()), 'outside candidates', int(((allpink >= 0.25) & ~np.isfinite(best)).sum()))
    print('scores of rejected: skirt', np.percentile(score[1][rej], [10, 50, 90]), 'sash', np.percentile(score[6][rej], [10, 50, 90]))
