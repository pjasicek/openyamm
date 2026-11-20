"""Where every texel of the new texture sets lies on the installed goblin: for each covered texel of
work/uvraster_{body,head}.npz the nearest point on the installed full-detail mesh (work/ladder.blend Body, rest pose,
merged 2080x1024 atlas UVs) -> its installed UV and the installed tangent frame there, plus the new mesh's tangent
frame at the texel (work/gob_master.blend). Lets compose_gob.py carry the installed normal map and shading detail onto
the new layout through the shared surface. Out: work/installed_lookup_{body,head}.npz
(uv [N,N,2] installed atlas uv or -1, t_old/b_old/n_old and t_new/b_new/n_new [N,N,3])."""
import os
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def frames(obj, uvname=None):
    """Per-loop tangent frame of a triangulated copy: (tris [T,3] vertex ids, loop uv [T,3,2], t/b/n [T,3,3])."""
    me = obj.data
    # smooth frames: the welded GLB import of the installed model carries sharp-face/custom-normal attributes (flat
    # facets), the runtime meshes are smooth
    for name in ('sharp_face', 'sharp_edge', 'custom_normal'):
        if name in me.attributes:
            me.attributes.remove(me.attributes[name])
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)) if hasattr(me.polygons[0], 'use_smooth') else None
    if any(len(p.vertices) > 4 for p in me.polygons):       # tangents need tris/quads (the cone caps are 6-gons)
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4]); bm.to_mesh(me); bm.free()
    if uvname:
        me.uv_layers.active = me.uv_layers[uvname]
    me.calc_tangents()
    me.calc_loop_triangles()
    tris = np.array([t.vertices[:] for t in me.loop_triangles])
    loops = np.array([t.loops[:] for t in me.loop_triangles])
    uv = np.array([l.uv[:] for l in me.uv_layers.active.data])[loops]
    t = np.array([l.tangent[:] for l in me.loops])[loops]
    n = np.array([l.normal[:] for l in me.loops])[loops]
    s = np.array([l.bitangent_sign for l in me.loops])[loops]
    b = np.cross(n, t) * s[..., None]
    return tris, uv, t, b, n, [tr.polygon_index for tr in me.loop_triangles]


def rest(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    rig = bpy.data.objects['Rig']; rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.matrix_basis.identity()
    bpy.context.view_layer.update()


# installed mesh: BVH over its triangles
rest(os.path.join(HERE, 'work', 'ladder.blend'))
old = bpy.data.objects['Body']
otris, ouv, ot, ob, on, _ = frames(old)
oco = np.array([v.co[:] for v in old.data.vertices])
bvh = BVHTree.FromPolygons([Vector(c) for c in oco], otris.tolist())

# new mesh frames, then texel lookups
rest(os.path.join(HERE, 'work', 'gob_master.blend'))
new = bpy.data.objects['Body']
ntris, nuv, nt, nb, nn, _ = frames(new)
nco = np.array([v.co[:] for v in new.data.vertices])
N = 1024


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(-1), (v0 * v1).sum(-1), (v1 * v1).sum(-1)
    d20, d21 = (v2 * v0).sum(-1), (v2 * v1).sum(-1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-20, 1e-20, d00 * d11 - d01 * d01)
    v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    return np.stack([1 - v - w, v, w], -1)


# new-mesh tangent frame per texel: rasterise the new triangles again (same rule as raster_gob.py)
for slot, label in enumerate(['body', 'head']):
    R = np.load(os.path.join(HERE, 'work', f'uvraster_{label}.npz'))
    cov = R['piece'] >= 0; pos = R['pos']
    out = {k: np.zeros((N, N, 3), np.float32) for k in ('t_new', 'b_new', 'n_new', 't_old', 'b_old', 'n_old')}
    uvo = np.full((N, N, 2), -1.0, np.float32)
    mats = [p.material_index for p in new.data.polygons]
    for k, tri in enumerate(ntris):
        if mats[new.data.loop_triangles[k].polygon_index] != slot:
            continue
        P = nuv[k] * N
        x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b_, c = P
        den = (b_[1] - c[1]) * (a[0] - c[0]) + (c[0] - b_[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b_[1] - c[1]) * (xs - c[0]) + (c[0] - b_[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w = np.stack([w0, w1, 1 - w0 - w1], -1)
        m = (w >= -0.02).all(-1)
        iy = (N - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)
        for key, arr in (('t_new', nt), ('b_new', nb), ('n_new', nn)):
            out[key][iy, ix] = w[m] @ arr[k]
    # installed: nearest surface point per covered texel
    idx = np.argwhere(cov)
    for (y, x) in idx:
        loc, _, f, _ = bvh.find_nearest(Vector(pos[y, x].tolist()))
        if f is None:
            continue
        bw = bary(np.array(loc[:]), *oco[otris[f]])
        uvo[y, x] = bw @ ouv[f]
        out['t_old'][y, x] = bw @ ot[f]; out['b_old'][y, x] = bw @ ob[f]; out['n_old'][y, x] = bw @ on[f]
    np.savez_compressed(os.path.join(HERE, 'work', f'installed_lookup_{label}.npz'), uv=uvo, **out)
    print('LOOKUP', label, int(cov.sum()), 'texels', 'found', int((uvo[..., 0] >= 0).sum()))
