#!/usr/bin/env python3
"""Step 1: card table of an installed MM6 tree (system Python).

Reads the installed source GLB (copied to work/<id>/installed.glb, the baseline for every gate) and the MM6 pipeline's
clump layout (`../mm6_new_sorpigal_3d/trees/work/<sid>/clumps.json`, groups.json; read only), and writes
work/<id>/cards.npz:
  per LOD l in 0..2: c<l>_corners (n, 4, 3) glTF coordinates, c<l>_clump (n,) clump id (LOD2: group id),
  c<l>_colour (n, 3) linear seen colour = mean COLOR_0 x the card's texel albedo (alpha >= 0.5, linear);
  c<l>_vc (n, 3) the mean COLOR_0 alone;
  clump_centre (k, 3), clump_radius (k,), clump_axes (k, 3) (per-axis spread of the clump's cards, glTF axes),
  group_centre / group_radius / group_members for LOD2.
Usage: prep.py <id>   (species/<id>.json: {"sid": "6tree01", "glb": "mm6_deco_tree01.glb", ...})"""
import io, json, os, shutil, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb, common

spec = common.load(sys.argv[1]); W = spec['work']
src = os.path.join(common.REPO, 'assets_source', 'engine', 'models', spec['glb'])
base = os.path.join(W, 'installed.glb')
backup = os.path.join(common.HERE, 'backup_pre_overdraw', spec['glb'])
if not os.path.exists(base):                 # the baseline is always the source from before this pass
    pre = backup if os.path.exists(backup) else src
    assert 'Shell' not in [x['name'] for x in glb.read(pre).doc['materials']], f'{pre} already has a shell'
    shutil.copy2(pre, base)
elif open(base, 'rb').read() != open(src, 'rb').read():
    print('WARNING installed source changed since work/<id>/installed.glb was taken:', src)
m = glb.read(base)
pipe = os.path.join(common.MM6_TREES, 'work', spec['sid'])
clumps = json.load(open(os.path.join(pipe, 'clumps.json')))['clumps']
groups = json.load(open(os.path.join(pipe, 'groups.json')))


def g(b):                                   # Blender z-up -> glTF y-up
    b = np.asarray(b, float)
    return np.stack([b[..., 0], b[..., 2], -b[..., 1]], -1)


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def albedo_table(prim):
    mat = m.doc['materials'][prim['material']]
    tex = m.doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    im = np.asarray(Image.open(io.BytesIO(m.images[tex])).convert('RGBA')).astype(np.float32) / 255
    return im


def card_colours(prim, im):
    pos = m.get(prim['attributes']['POSITION']).reshape(-1, 4, 3)
    col = m.get(prim['attributes']['COLOR_0'])[:, :3].reshape(-1, 4, 3).mean(1)
    uv = m.get(prim['attributes']['TEXCOORD_0']).reshape(-1, 4, 2)
    h, w = im.shape[:2]; cache = {}; alb = []
    for k in range(len(uv)):
        lo = uv[k].min(0); hi = uv[k].max(0)
        key = tuple(np.round(np.concatenate([lo, hi]), 3))
        if key not in cache:
            x0, x1 = int(np.clip(lo[0] * w, 0, w - 1)), int(np.clip(np.ceil(hi[0] * w), 1, w))
            y0, y1 = int(np.clip(lo[1] * h, 0, h - 1)), int(np.clip(np.ceil(hi[1] * h), 1, h))
            cell = im[y0:y1, x0:x1].reshape(-1, 4)
            ok = cell[:, 3] >= 0.5
            cache[key] = srgb_to_lin(cell[ok, :3]).mean(0) if ok.any() else np.full(3, 0.1)
        alb.append(cache[key])
    return pos, col * np.array(alb), col


out = {}
chain = m.mesh_chain()
centres = g([c['centre'] for c in clumps]); radii = np.array([c['radius'] for c in clumps])
lod0_owner = np.concatenate([[ci] * len(c['cards']) for ci, c in enumerate(clumps)]).astype(int)
lod0_centres = np.concatenate([g([cd['corners'] for cd in c['cards']]).mean(1) for c in clumps])
for lod in (0, 1, 2):
    prim = m.primitive(chain[lod], 'LeavesFar' if lod == 2 else 'Leaves')
    if prim is None:
        prim = m.primitive(chain[lod], 'Leaves')
    pos, colour, vc = card_colours(prim, albedo_table(prim))
    out[f'c{lod}_vc'] = vc                       # mean COLOR_0 (the baked occlusion x tint), without the texture
    if lod < 2:
        d, ii = cKDTree(lod0_centres).query(pos.mean(1))
        assert d.max() < 0.05, f'LOD{lod} cards do not match clumps.json ({d.max():.4f} m)'
        owner = lod0_owner[ii]
    else:
        assert len(pos) == 4 * len(groups), (len(pos), len(groups))
        owner = np.arange(len(pos)) // 4
    out[f'c{lod}_corners'] = pos; out[f'c{lod}_clump'] = owner; out[f'c{lod}_colour'] = colour
    print(f'PREP LOD{lod} cards {len(pos)} mean colour (linear) {colour.mean(0).round(3).tolist()}')
axes = []
for ci, c in enumerate(clumps):
    pts = lod0_centres[lod0_owner == ci]
    spread = pts.std(0) if len(pts) > 3 else np.full(3, radii[ci] * 0.5)
    axes.append(spread / max(spread.mean(), 1e-6))     # relative per-axis shape (mean 1)
out['clump_centre'] = centres; out['clump_radius'] = radii; out['clump_axes'] = np.array(axes)
out['clump_inner'] = np.array([c['inner'] for c in clumps])
out['group_centre'] = g([gr['centre'] for gr in groups]); out['group_radius'] = np.array([gr['radius'] for gr in groups])
out['group_members'] = np.array(json.dumps([gr['members'] for gr in groups]))
np.savez(os.path.join(W, 'cards.npz'), **out)
print('PREP', spec['id'], 'clumps', len(clumps), 'groups', len(groups), '->', os.path.join(W, 'cards.npz'))
