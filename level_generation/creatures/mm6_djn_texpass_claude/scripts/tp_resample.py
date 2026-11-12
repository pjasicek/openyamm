"""Carries the approved (installed) maps onto a texture-pass layout at the same surface points: each texel of the new
layout finds its triangle and barycentrics, takes that point's old UV and samples the old image of the triangle's
primitive (its default material): colour, burn map bilinear, region mask bilinear (primitives without a mask: 0),
metal/roughness nearest (classes). Gutters are padded with the nearest island texel. The normal map is not carried
(tangent frames differ per chart).

Usage: tp_resample.py <layout npz> <out prefix> [colour size 2048] [mask/mr/burn size; default: the installed size]
Writes <out prefix>_{basecolor,region_mask,metal_rough,burn_map}.png, <out prefix>_raster<size>.npz (triangle id and
barycentrics per texel) and <out prefix>_prim<size>.png is not written (prim per texel = layout prim[tri_id]).
"""
import sys

import numpy as np
from PIL import Image

import tp_common as C
import texlib

cfg = C.config()
layout_path, prefix = sys.argv[1], sys.argv[2]
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else cfg.get('size', 2048)
SMALL = int(sys.argv[4]) if len(sys.argv) > 4 else 1024
layout = np.load(layout_path)
before = np.load(C.lod0_path())
old_uv = before['uv'][before['tri']]
prim_of_tri = before['prim']
g = C.Glb(C.before_glb(cfg))
doc = g.doc
mesh = doc['meshes'][C.lod0_mesh_index(doc, cfg['node'])]
sources = {pi: C.material_maps(doc['materials'][mesh['primitives'][pi]['material']]) for pi in cfg['atlas_prims']}
cache = {}


def picture(texture, mode):
    key = (texture, mode)
    if key not in cache:
        cache[key] = np.asarray(g.image(doc['textures'][texture]['source']).convert(mode), np.float32)
    return cache[key]


def installed_size(kind):
    """The installed map's size (largest side over the atlas primitives), at most SIZE; SMALL when given."""
    if len(sys.argv) > 4:
        return SMALL
    sides = [max(g.image(doc['textures'][m[kind]]['source']).size) for m in sources.values() if kind in m]
    return min(SIZE, max(sides))


for kind, size, mode in (('basecolor', SIZE, 'RGB'), ('region_mask', None, 'RGBA'), ('metal_rough', None, 'RGB'),
                         ('burn_map', None, 'RGB')):
    if not any(kind in s for s in sources.values()):
        continue
    size = size or installed_size(kind)
    raster_path = f'{prefix}_raster{size}.npz'
    try:
        r = np.load(raster_path)
        tri_id, bary = r['tri_id'], r['bary']
    except FileNotFoundError:
        tri_id, bary = texlib.raster(layout['uv'], size)
        np.savez_compressed(raster_path, tri_id=tri_id, bary=bary)
    cov, uv = texlib.corresponding_uv(tri_id, bary, old_uv)
    tprim = prim_of_tri[tri_id[cov]]
    channels = 4 if mode == 'RGBA' else 3
    values = np.zeros((len(uv), channels), np.float32)
    for pi, maps in sources.items():
        sel = tprim == pi
        if kind not in maps or not sel.any():
            continue
        img = picture(maps[kind], mode)
        values[sel] = texlib.nearest(img, uv[sel]) if kind == 'metal_rough' else texlib.bilinear(img, uv[sel])
    out = np.zeros((size, size, channels), np.float32)
    out[cov] = values
    out = texlib.pad(out, cov)
    Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), mode).save(f'{prefix}_{kind}.png')
    print('WROTE', f'{prefix}_{kind}.png', f'{cov.mean():.1%} covered')

# ---- approved normal map in the new layout's tangent frames (fs_model.sc builds the frame per pixel from position and
# UV derivatives, i.e. per triangle from its edges and UVs): the old shaded normal (interpolated normal + old map at the
# material's scale) rebuilt in the old frame and stored in the new triangle's frame, as transfer_textures.py does for
# far LODs. Kept so a normal map baked from a denser mesh (Codex rebake reductions) is not lost.
import types  # noqa: E402
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(C.CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

mat = doc['materials'][mesh['primitives'][cfg['atlas_prims'][0]]['material']]
if 'normal' in C.material_maps(mat):
    scale = mat['normalTexture'].get('scale', 1.0)
    r = np.load(f'{prefix}_raster{SIZE}.npz')
    tri_id, bary = r['tri_id'], r['bary']
    cov = tri_id >= 0
    t = tri_id[cov]
    b = bary[cov]
    pos, nrm = before['pos'], before['nrm']
    tri = before['tri']
    new_uv = layout['uv']
    shading = TT.normalize((b[:, :, None] * TT.normalize(nrm)[tri[t]]).sum(1))
    e1, e2 = pos[tri[t, 1]] - pos[tri[t, 0]], pos[tri[t, 2]] - pos[tri[t, 0]]
    ou = old_uv[t]
    t0, b0 = TT.frame(e1, e2, ou[:, 1] - ou[:, 0], ou[:, 2] - ou[:, 0], shading)
    xy = np.zeros((len(t), 2), np.float32)
    for pi, maps in sources.items():
        sel = prim_of_tri[t] == pi
        if 'normal' in maps and sel.any():
            img = picture(maps['normal'], 'RGB')
            xy[sel] = texlib.bilinear(img, (b[sel][:, :, None] * ou[sel]).sum(1))[:, :2] / 127.5 - 1.0
    z = np.sqrt(np.maximum(1.0 - (xy ** 2).sum(-1), 0.0))
    target = TT.normalize(t0 * (xy[:, :1] * scale) - b0 * (xy[:, 1:] * scale) + shading * z[:, None])
    nu = new_uv[t]
    t1, b1 = TT.frame(e1, e2, nu[:, 1] - nu[:, 0], nu[:, 2] - nu[:, 0], shading)
    basis = np.stack([t1, -b1, shading], -1)
    coef = np.linalg.solve(basis + np.eye(3) * 1e-9, target[:, :, None])[:, :, 0]
    coef[:, 2] = np.maximum(coef[:, 2], 0.05)
    coef = TT.normalize(coef)
    coef[:, :2] /= scale                              # the engine applies the material's scale again
    coef = TT.normalize(coef)
    out = np.zeros((SIZE, SIZE, 3), np.float32)
    out[cov] = coef * 127.5 + 127.5
    out = texlib.pad(out, cov)
    Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8)).save(f'{prefix}_normal.png')
    print('WROTE', f'{prefix}_normal.png', f'(material normal scale {scale})')
