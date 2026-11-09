"""Step B: head-only Meshy parts on the fitted body. The old head and the hair spikes down the back go; the head's neck stub is opened inside an ellipse (the mane behind it stays), its ring conforms to the body's and they are bridged, so the skin is
one connected shell (now done by the wrap, see wrap_voxel.py and wrap_finish.py). Horns are scaled at the root. Parts: 0 body skin, 10 head shell (face, mane, ears), 12 horns, 13 eyes, 14 teeth, 15 mouth plug.
Writes the assembled triangles for wrap_voxel.py. Args: <pose blend> <head blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector, Matrix
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OY, OZ = 0.655, -0.103, 0.9465
HORN = 0.8; HORN_ROOT = np.array([0.165, -0.11, 0.15])
C = np.array([0.0, -0.03, 0.755]); N = np.array([0.0, -0.35, 0.937]); N /= np.linalg.norm(N)
HF = 0.015; FALL = 0.10
U = np.array([1.0, 0, 0]); V = np.cross(N, U)
BACK = ((0.42, 0.34), (0.5, 0.325), (0.6, 0.30), (0.7, 0.255), (0.8, 0.19), (0.9, 0.12))     # the back's profile under the old hair spikes, |x| < 0.26
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 10, 'Horns': 12, 'Eyes': 13, 'Teeth': 14}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.verts.layers.int.new('part')
# old head off
hh = lambda p: (p - C) @ N
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=C, plane_no=N, clear_outer=True)
# hair spikes flattened onto the back
zz = np.array([b[0] for b in BACK]); yy = np.array([b[1] for b in BACK])
pts = [v for v in bm.verts if v.co.z > 0.4 and abs(v.co.x) < 0.3]
moved = []
for v in pts:
    ym = np.interp(v.co.z, zz, yy) + 0.02 * (abs(v.co.x) / 0.3) ** 2
    if v.co.y > ym: v.co.y = ym; moved.append(v)
print('SPIKES', len(moved))
mv_set = {x for v in moved for e in v.link_edges for x in (v, e.other_vert(v))}
for _ in range(3):
    mv_set |= {e.other_vert(v) for v in mv_set for e in v.link_edges}
for _ in range(30):
    nw = {}
    for v in mv_set:
        if v.is_boundary: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        nw[v] = v.co * 0.4 + (sum(nb, Vector()) / len(nb)) * 0.6
    for v, c in nw.items(): v.co = c
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    if nm == 'Horns':
        for v in t.verts:
            p = np.array(v.co[:]); r = HORN_ROOT * [np.sign(p[0]), 1, 1]
            v.co = Vector(r + (p - r) * HORN)
    for v in t.verts: v.co = Vector((v.co.x * S, v.co.y * S + OY, v.co.z * S + OZ))
    tl = t.verts.layers.int.new('part')
    for v in t.verts: v[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    lay = bm.verts.layers.int['part']
    bpy.data.meshes.remove(tm)
# mouth plug: dark ellipsoid behind the teeth
r_ = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0, matrix=Matrix.Translation((0, -0.262, 0.795)) @ Matrix.Diagonal((0.105, 0.05, 0.05, 1)))
for v in r_['verts']: v[lay] = 15
# eye plugs: the sockets end behind the eyeballs, which come back as separate pieces after the wrap
for sx in (1, -1):
    r_ = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.021, matrix=Matrix.Translation((sx * 0.057, -0.301, 0.919)))
    for v in r_['verts']: v[lay] = 15
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
pa = np.array([v[lay] for v in bm.verts]); co = np.array([v.co[:] for v in bm.verts])
tri = np.array([[v.index for v in f.verts] for f in bm.faces])
print('ASSEMBLED', len(co), len(tri), {int(k): int((pa == k).sum()) for k in np.unique(pa)})
np.savez(OUT, co=co, tri=tri, part=pa)
