"""Head-only Meshy parts on the body. The old neck keeps only the V under the plane; the new neck runs down inside the collar (the old neck is no closed ring here, so no bridge).
Old note (mm9_thrall_claude/scripts/graft_thrall.py): The old neck (part 2, Meshy's own, it carries the bare V of the chest under the collar) and the new face are cut on one tilted
plane across the neck, the face's neck conforms to the old ring and they are bridged, so the skin is one shell. Hair and eyes go in as parts 21, 22; the face is part 20.
Args: <fit blend> <head blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
OFF = np.array([0.0, 0.02, 0.795])
C = np.array([0.0, 0.03, 0.65]); N = np.array([0.0, -0.45, 0.893]); N /= np.linalg.norm(N)
U = np.array([1.0, 0, 0]); V = np.cross(N, U)
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 20, 'Helm': 21, 'Eyes': 22}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.faces.layers.int['part']
fs = [f for f in bm.faces if f[lay] == 2]; vs = list({v for f in fs for v in f.verts}); es = list({e for f in fs for e in f.edges})
bmesh.ops.bisect_plane(bm, geom=vs + es + fs, plane_co=C, plane_no=N, clear_outer=True)
bm.faces.ensure_lookup_table()
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co += Vector(OFF)
    tl = t.faces.layers.int.new('part')
    for f in t.faces: f[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
# the coif's rim: MM9's hangs through the shoulders. Each rim vertex goes to 1.8 cm above the shoulder under it, the sheet below ear height is compressed to it, by angle round the neck
from mathutils.bvhtree import BVHTree
lay = bm.faces.layers.int['part']
bm.verts.ensure_lookup_table()
bodyf = [f for f in bm.faces if f[lay] in (1, 8, 13)]
T_ = bmesh.new(); vm = {}
for f in bodyf:
    for v in f.verts:
        if v not in vm: vm[v] = T_.verts.new(v.co)
    try: T_.faces.new([vm[v] for v in f.verts])
    except ValueError: pass
bvb = BVHTree.FromBMesh(T_)
hv = {v for f in bm.faces if f[lay] == 21 for v in f.verts}
seen = set(); comps = []
for v in hv:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    comps.append(cur)
coif = max(comps, key=len)
ZE = 0.815; yc = 0.045
rimv = [v for v in coif if v.co.z < 0.625]
Ang = np.arctan2([v.co.y - yc for v in rimv], [v.co.x for v in rimv]); Rz = np.array([v.co.z for v in rimv])
Tz = []
for v in rimv:
    loc, nor, idx, dist = bvb.ray_cast(Vector((v.co.x, v.co.y, 0.95)), Vector((0, 0, -1)), 0.5)
    Tz.append((loc.z if loc is not None else 0.60) + 0.018)
Tz = np.array(Tz)
bins = np.linspace(-np.pi, np.pi, 49); ctr = (bins[:-1] + bins[1:]) / 2
Rb = np.full(48, np.nan); Tb = np.full(48, np.nan)
for k in range(48):
    m = (Ang >= bins[k]) & (Ang < bins[k + 1])
    if m.any(): Rb[k] = Rz[m].min(); Tb[k] = Tz[m].max()
ok = ~np.isnan(Rb)
Rb = np.interp(ctr, ctr[ok], Rb[ok], period=2 * np.pi); Tb = np.interp(ctr, ctr[ok], Tb[ok], period=2 * np.pi)
Tb = np.maximum(Tb, 0.672)                                     # level enough at the back: MM9's rim is square, not a point
Tb = 0.5 * (Tb + Tb[::-1][np.r_[24:48, 0:24]])
for _ in range(6): Tb = 0.5 * Tb + 0.25 * (np.roll(Tb, 1) + np.roll(Tb, -1))
print('COIF rim z', round(float(Rb.min()), 3), 'to target', np.round(Tb[[0, 12, 24, 36]], 3), 'n', len(rimv))
for v in coif:
    if v.co.z >= ZE: continue
    a = np.arctan2(v.co.y - yc, v.co.x)
    r = np.interp(a, ctr, Rb, period=2 * np.pi); t = np.interp(a, ctr, Tb, period=2 * np.pi)
    v.co.z = ZE + (v.co.z - ZE) * (ZE - t) / max(ZE - r, 1e-3)
T_.free()
seen = set(); drop = []
for v in {v for f in bm.faces if f[lay] == 2 for v in f.verts}:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    if len(cur) < 12: drop += cur
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
