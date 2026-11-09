"""PeasantHOF2 (row 64, the prisoner) as a variant of the HOF1 Meshy body (same 86-node skeleton; MM9's HOF2 mesh differs
in the dress length and the head: a floor-length skirt and a cream kerchief over the head to the shoulders instead of
the braids; its long sleeves are paint on the same arm mesh, as in MM9).

On the fitted, unreduced HOF1 body (work/fit_v1.blend, MM9 frame, 'Body'), positions and parts only:
1. Deleted: the four braids, the shawl knot and its hanging ends (HOF2 has neither).
2. Skirt and apron lengthened: below Z0 every vertex's height is stretched about Z0 so the hem reaches HEM (skirt) or
   APRON (apron), with a gentle radial flare toward the hem (FLARE at the hem) about the skirt's vertical axis.
3. Kerchief: a new part 'kerchief' over the head down to the shoulders: rays from the head centre C to the convex hull of
   the head, neck and shoulder tops (back half), hit + OFF; directions inside the face cone (half-angle from 68 deg at
   the crown to 100 deg at ear height, so the drape passes behind the ears) and the front below the chin are left
   open; the drape is cut at ZB (on the shoulders). A grid in (azimuth about the forward axis, polar angle).
Writes <out blend> (Body only, unweighted parts carry no groups: fit_rig.py re-weights the whole body) and <out glb>
(the static Body for fit_rig.py). Args: <in blend> <out blend> <out glb>"""
import bpy, bmesh, sys, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
for o in list(bpy.data.objects):
    if o is not ob:
        bpy.data.objects.remove(o)
ob.parent = None
ob.modifiers.clear()
ob.vertex_groups.clear()
Z0, HEM, APRON, FLARE = -0.08, -0.925, -0.60, 0.10
OFF, ZB = 0.012, 0.535
C = np.array([0.0, 0.045, 0.80])

bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); parts = []
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = len(parts); cur = []
    while st:
        x = st.pop(); cur.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = len(parts); st.append(o)
    parts.append(cur)
CO = np.array([v.co[:] for v in bm.verts])
def centre(p): q = CO[p]; return 0.5 * (q.min(0) + q.max(0))
DROP = [(0.102, -0.058, 0.644), (-0.114, -0.057, 0.645), (0.058, 0.253, 0.609), (-0.065, 0.253, 0.609),   # braids
        (-0.007, -0.15, 0.508), (-0.043, -0.197, 0.417), (0.027, -0.195, 0.415), (-0.033, -0.19, 0.421),
        (0.021, -0.192, 0.413)]                                                                              # knot, ends
drop = []; skirt = apron = None
for k, p in enumerate(parts):
    c = centre(p)
    if any(np.linalg.norm(c - np.array(d)) < 0.01 for d in DROP):
        drop += p; print('DROP part', len(p), np.round(c, 3).tolist())
    if np.linalg.norm(c - np.array([-0.002, 0.035, -0.142])) < 0.01: skirt = p
    if np.linalg.norm(c - np.array([0.003, -0.153, -0.035])) < 0.01: apron = p
assert skirt is not None and apron is not None
for name, p, target in (('skirt', skirt, HEM), ('apron', apron, APRON)):
    q = CO[p]; zmin = q[:, 2].min()
    s = (Z0 - target) / (Z0 - zmin)
    ax = np.array([np.median(CO[skirt][:, 0]), np.median(CO[skirt][:, 1])])
    for i in p:
        z = CO[i, 2]
        if z >= Z0: continue
        z2 = Z0 + (z - Z0) * s
        t = (Z0 - z2) / (Z0 - HEM)
        r = CO[i, :2] - ax
        CO[i, :2] = ax + r * (1 + FLARE * t ** 1.5)
        CO[i, 2] = z2
        bm.verts[i].co = Vector(CO[i].tolist())
    print('STRETCH', name, 'hem', round(float(zmin), 3), '->', target, 'factor', round(s, 3))
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in drop], context='VERTS')
bm.verts.ensure_lookup_table()

# ---- kerchief: convex hull of head/neck/shoulder-top vertices (no ears: none in this body yet)
pts = [v.co.copy() for v in bm.verts if (v.co.z > 0.62 and abs(v.co.x) < 0.2) or
       (v.co.z > ZB - 0.05 and abs(v.co.x) < 0.27 and v.co.y > -0.02)]
hb = bmesh.new()
hv = [hb.verts.new(p) for p in pts]
bmesh.ops.convex_hull(hb, input=hv)
for v in [v for v in hb.verts if not v.link_faces]:
    hb.verts.remove(v)
bvh = BVHTree.FromBMesh(hb)
fwd = np.array([0, -1.0, 0]); up = np.array([0, 0, 1.0]); side = np.array([1.0, 0, 0])
NA, NB = 30, 72                    # polar steps (from the face-cone edge to straight back), azimuth steps
def direction(alpha, beta):
    # alpha: angle from forward; beta: azimuth about the forward axis (0 = up, +90 = creature's -x side? sign below)
    d = fwd * math.cos(alpha) + math.sin(alpha) * (up * math.cos(beta) + side * math.sin(beta))
    return d / np.linalg.norm(d)
def inside(alpha, beta):
    d = direction(alpha, beta)
    el = math.asin(max(-1.0, min(1.0, d[2])))                          # elevation above the horizontal
    a0 = math.radians(68 + 32 * (1 - min(1.0, abs(el) / math.radians(60)))) if el > 0 else math.radians(100)
    if alpha < a0: return False
    if d[2] < -0.05 and d[1] < 0.25: return False                       # no sheet under the chin / at the front
    return True
grid = {}
for i in range(NA + 1):
    alpha = math.radians(60) + (math.pi - math.radians(60)) * i / NA
    for j in range(NB):
        beta = 2 * math.pi * j / NB
        if not inside(alpha, beta): continue
        d = direction(alpha, beta)
        hit = bvh.ray_cast(Vector(C.tolist()), Vector(d.tolist()), 2.0)
        if hit[0] is None: continue
        p = np.array(hit[0][:]) + d * OFF
        if p[2] < ZB: continue
        grid[(i, j)] = p
kb = bm
lay = kb.faces.layers.int.get('kerchief') or kb.faces.layers.int.new('kerchief')
nv = {k: kb.verts.new(Vector(p.tolist())) for k, p in grid.items()}
nf = 0
for i in range(NA):
    for j in range(NB):
        q = [(i, j), (i, (j + 1) % NB), (i + 1, (j + 1) % NB), (i + 1, j)]
        if all(k in nv for k in q):
            try:
                f = kb.faces.new([nv[k] for k in q]); f[lay] = 1; f.smooth = True; nf += 1
            except ValueError:
                pass
loose = [v for v in nv.values() if not v.link_faces]
for v in loose: kb.verts.remove(v)
kf = [f for f in kb.faces if f[lay]]
bmesh.ops.remove_doubles(kb, verts=list({v for f in kf for v in f.verts}), dist=1e-4)
kf = [f for f in kb.faces if f.is_valid and f[lay]]
bmesh.ops.recalc_face_normals(kb, faces=kf)
# outward normals: the kerchief's faces must face away from C
cnt = sum(1 for f in kf if (np.array(f.calc_center_median()[:]) - C) @ np.array(f.normal[:]) < 0)
if cnt > len(kf) / 2:
    bmesh.ops.reverse_faces(kb, faces=kf)
# soften the open rim: two relax passes over boundary vertices along the boundary
for _ in range(3):
    bv = [v for f in kf for v in f.verts if v.is_boundary]
    new = {}
    for v in set(bv):
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            new[v] = (v.co * 2 + nb[0].co + nb[1].co) / 4
    for v, c in new.items(): v.co = c
bmesh.ops.triangulate(kb, faces=[f for f in kb.faces if f.is_valid and f[lay]])
print('KERCHIEF faces', sum(1 for f in kb.faces if f[lay]), 'grid points', len(grid))
bm.to_mesh(me); me.update()
print('VARIANT tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
for o in bpy.data.objects: o.select_set(o is ob)
bpy.context.view_layer.objects.active = ob
# undo the Blender Z-up import frame: export as glTF Y-up (fit_rig imports it back the same way)
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
for p in me.polygons:
    p.use_smooth = True
bpy.ops.export_scene.gltf(filepath=a[2], use_selection=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_texcoords=False, export_normals=False)
print('VARIANT saved', a[1], a[2])
