"""Shape fixes on the UV master; vertices move, UVs and topology stay, so the paint holds. Second pass of the coordinator review.
- Collar: Meshy's neck cone above the ruff (a blunt cap, since the head floats free) is cut off on one plane, a clean rim, and a dark bowl goes in under it. The bowl's faces take a dark patch in free atlas space. This one changes topology on the jacket, never touching its UVs.
- Head: the back of the head follows MM9's profile (work/mm9_head_profile.npz): the hair mass tapers to the nape, hood-like, instead of ending in a bob over a step at the jaw.
Args: <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]
Z0 = 0.462
bpy.ops.wm.open_mainfile(filepath=A[0])
body = bpy.data.objects['Body']; head = bpy.data.objects['Head']
import bmesh, json
from mathutils import Vector
me = body.data
dark = json.load(open(os.path.join(os.path.dirname(A[0]), 'collar_uv.json')))['uv']
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv['UVMap']; pl = bm.faces.layers.int['part']; hl = bm.faces.layers.int['hand']
faces = [f for f in bm.faces if not f[pl] and not f[hl] and abs(f.calc_center_median().x) < 0.17 and f.calc_center_median().z > 0.42]
geom = faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, Z0), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.edges.ensure_lookup_table()
ring = [e for e in bm.edges if e.is_boundary and all(abs(v.co.z - Z0) < 2e-4 for v in e.verts)]
left = set(ring); loops = []
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
loops.sort(key=len, reverse=True)
print('COLLAR rim loops', [len(l) for l in loops])
rim = list(loops[0])
vs = list({v for e in rim for v in e.verts}); cen = sum((v.co for v in vs), Vector()) / len(vs)
# inner flaps of Meshy's collar under the rim: they would draw over the bowl
import math
pts = [(math.atan2(v.co.y - cen.y, v.co.x - cen.x), math.hypot(v.co.x - cen.x, v.co.y - cen.y)) for v in vs]


def rim_r(a):
    return max((r for t, r in pts if abs(math.atan2(math.sin(t - a), math.cos(t - a))) < 0.5), default=0.1)


fl = [f for f in bm.faces if not f[pl] and not f[hl] and 0.36 < f.calc_center_median().z < Z0 + 1e-3 and abs(f.calc_center_median().x) < 0.14]
drop_f = []
rimset = set(rim)
for f in fl:
    c = f.calc_center_median()
    a = math.atan2(c.y - cen.y, c.x - cen.x)
    if math.hypot(c.x - cen.x, c.y - cen.y) < 0.8 * rim_r(a) and not (set(f.edges) & rimset) and not (set(v for v in f.verts) & set(vs)):
        drop_f.append(f)
print('COLLAR inner flaps', len(drop_f))
bmesh.ops.delete(bm, geom=drop_f, context='FACES')
bm.edges.ensure_lookup_table()
rim = [e for e in rim if e.is_valid]
new = []
for scale, drop in ((0.8, 0.018), (0.45, 0.034)):
    ex = bmesh.ops.extrude_edge_only(bm, edges=rim)
    nv = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]
    rim = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMEdge) and all(v in nv for v in g.verts)]
    new += [g for g in ex['geom'] if isinstance(g, bmesh.types.BMFace)]
    for v in nv:
        v.co = Vector((cen.x + (v.co.x - cen.x) * (scale / (1.0 if scale == 0.8 else 0.8)), cen.y + (v.co.y - cen.y) * (scale / (1.0 if scale == 0.8 else 0.8)), Z0 - drop))
cv = bm.verts.new((cen.x, cen.y, Z0 - 0.042))
for e in rim:
    new.append(bm.faces.new((e.verts[0], e.verts[1], cv)))
for f in new:
    f[pl] = 0; f[hl] = 0
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    for l in f.loops:
        l[uvl].uv = dark
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='FIXED')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
print('COLLAR bowl faces', len(new))
# head: per height, the back half scaled to MM9's depth, and narrowed to MM9's width behind the ears
d = np.load(os.path.join(os.path.dirname(A[0]), 'mm9_head_profile.npz'))
zs, ymax_m, xmax_m = d['z'], d['ymax'], d['xmax']
hm = head.data
co = np.array([v.co[:] for v in hm.vertices])
YC = -0.2
ours_y = np.array([co[np.abs(co[:, 2] - z) < 0.012, 1].max() if (np.abs(co[:, 2] - z) < 0.012).any() else np.nan for z in zs])
ours_x = np.array([np.abs(co[np.abs(co[:, 2] - z) < 0.012, 0]).max() if (np.abs(co[:, 2] - z) < 0.012).any() else np.nan for z in zs])
print('PROFILE z', zs.round(3), '\n ours y', ours_y.round(3), '\n mm9 y', ymax_m.round(3), '\n ours x', ours_x.round(3), '\n mm9 x', xmax_m.round(3))
ry = np.clip((ymax_m - YC) / np.maximum(ours_y - YC, 1e-3), 0.3, 1.0)
rx = np.clip(xmax_m / np.maximum(ours_x, 1e-3), 0.6, 1.0)
ry = np.nan_to_num(ry, nan=1.0); rx = np.nan_to_num(rx, nan=1.0)
ry = np.convolve(np.pad(ry, 2, mode='edge'), np.ones(5) / 5, 'valid'); rx = np.convolve(np.pad(rx, 2, mode='edge'), np.ones(5) / 5, 'valid')
for v, c in zip(hm.vertices, co):
    b = np.clip((c[1] - YC) / 0.05, 0, 1); b = b * b * (3 - 2 * b)        # the face stays
    if b <= 0:
        continue
    fy = np.interp(c[2], zs, ry); fx = np.interp(c[2], zs, rx)
    v.co.y = YC + (c[1] - YC) * (1 + (fy - 1) * b) if c[1] > YC else c[1]
    v.co.x = c[0] * (1 + (fx - 1) * b)
hm.update(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=A[1])
print('SHAPED')
