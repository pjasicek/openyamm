"""Kira's braid (MM9: one thin braid behind her right ear hanging in front of the right shoulder, on the Yp* chain). Meshy fused it into
a stub (dropped in clean_kira.py); this builds it on the fitted body before the UVs, so the paid paint covers it: an 8-sided tube with
three-strand plait bulges (a lobe every 2.4 cm, alternating sides), tapering to a tie and a short tuft. The path's upper part runs
inside the hair behind the ear, the lower part lies 4 mm in front of the body (rays along +y). The Yp* joints move onto the path at
MM9's relative spacing (translation only, MM9's rest rotations kept). Part 23. Args: <fit blend> <out blend>"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
R0, R1 = 0.011, 0.0075
# control points (figure's right = -x); y None = lie on the body
CP = [(-0.070, 0.050, 0.725), (-0.083, 0.030, 0.675), (-0.093, None, 0.615), (-0.098, None, 0.560), (-0.101, None, 0.505),
      (-0.103, None, 0.455)]
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.faces.layers.int['part']
bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm)
pts = []
for x, y, z in CP:
    if y is None:
        hit = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
        y = hit[0].y - R0 - 0.004
        print('BRAID surface', x, z, round(hit[0].y, 4), 'part', bm.faces[hit[2]][lay] if hit[2] is not None else None)
    pts.append(np.array([x, y, z]))
pts = np.array(pts)
# resample along a Catmull-Rom curve at 5 mm
def cr(p, n=40):
    out = []
    P = np.vstack([p[0] * 2 - p[1], p, p[-1] * 2 - p[-2]])
    for i in range(1, len(P) - 2):
        for t in np.linspace(0, 1, n, endpoint=False):
            a, b, c, d = P[i - 1:i + 3]
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    out.append(P[-2]); return np.array(out)
C = cr(pts)
seg = np.linalg.norm(np.diff(C, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]; L = s[-1]
ns = int(L / 0.0065); sq = np.linspace(0, L, ns + 1)
C = np.array([np.interp(sq, s, C[:, k]) for k in range(3)]).T
T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
print('BRAID length', round(L, 3), 'samples', len(C))
SIDES = 8; LOBE = 0.024
rings = []
nb = bm.verts.layers.int.new('braid') if 'braid' not in bm.verts.layers.int else bm.verts.layers.int['braid']
ref = np.array([1.0, 0.0, 0.0])
for i, (c, t) in enumerate(zip(C, T)):
    u = sq[i] / L
    n1 = ref - t * (ref @ t); n1 /= np.linalg.norm(n1); n2 = np.cross(t, n1)
    r = R0 + (R1 - R0) * u
    tie = u > 0.93
    if tie: r = R1 * (0.75 if u < 0.95 else 1.15 - 2.5 * (u - 0.95))
    ring = []
    ph = sq[i] / LOBE * 2 * math.pi
    for k in range(SIDES):
        a = 2 * math.pi * k / SIDES
        side = 1 if math.cos(a) > 0 else -1
        bulge = 1.0 if tie else 1.0 + 0.16 * max(0.0, math.sin(ph + (0 if side > 0 else math.pi))) * abs(math.cos(a)) - 0.06 * abs(math.sin(ph * 2))
        p = c + (n1 * math.cos(a) + n2 * math.sin(a) * 0.82) * r * bulge
        v = bm.verts.new(Vector(p)); v[nb] = 1; ring.append(v)
    rings.append(ring)
new_faces = []
for a, b in zip(rings[:-1], rings[1:]):
    for k in range(SIDES):
        f = bm.faces.new((a[k], a[(k + 1) % SIDES], b[(k + 1) % SIDES], b[k])); new_faces.append(f)
for ring, cc in ((rings[0], C[0]), (rings[-1], C[-1])):
    cv = bm.verts.new(Vector(cc)); cv[nb] = 1
    for k in range(SIDES):
        new_faces.append(bm.faces.new((ring[k], ring[(k + 1) % SIDES], cv)))
for f in new_faces: f[lay] = 23; f.smooth = True
res = bmesh.ops.triangulate(bm, faces=new_faces)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[lay] == 23])
bm.to_mesh(me); bm.free()
# Yp joints on the path at MM9's relative spacing
names = ['Yponybase', 'Ypony', 'Yponypiv', 'YpA', 'YpB', 'YpC']
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
src = np.array([[-0.085, -0.063, 0.76], [-0.085, -0.067, 0.72], [-0.085, -0.079, 0.68], [-0.087, -0.108, 0.619], [-0.089, -0.14, 0.572], [-0.089, -0.168, 0.54]])
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(src, axis=0), axis=1))]
frac = d / (d[-1] + 0.06)          # MM9's last bone carries a 6 cm tip
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
Mi = arm.matrix_world.inverted()
for nm, f in zip(names, frac):
    p = np.array([np.interp(f * L, sq, C[:, k]) for k in range(3)])
    e = arm.data.edit_bones[nm]; v = Mi @ Vector(p) - e.head; e.head += v; e.tail += v
    print('BRAID joint', nm, np.round(p, 3).tolist())
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('BRAID done', len(C), 'rings')
