"""hkr: the Kreegan horns (concept 07_kreegan_castes.png / fam_troopers.png: two large ivory horns rising from the
temples, curving up and out, the tips turning in). The MM6 Demon has none (big ears, no horns), so every Kreegan
body gets them: part of the shared body mesh, rigid on the head (mixamorig:Head -> B_Head), material Demon_Body_A
with their UVs on an ivory patch of the body atlas (pixels x 1935..1991, y 98..246 of the 2K base colour: painted
spike ivory outside every region mask, so the horns stay ivory in every tier).
Each horn: a centreline (cubic Bezier through CTRL, mirrored for the right), 8 sides, NSEG rings with the radius
tapering R0 -> tip (flattened 15 % front-back), the root ring sunk 1.5 cm into the skull, the tip closed by a point.
Adds pieces 35/36 (garment 3, head-rigid). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
body = bpy.data.objects['Body']; me = body.data
CTRL = [(0.040, -0.285, 1.640), (0.118, -0.287, 1.685), (0.172, -0.268, 1.790), (0.128, -0.240, 1.880)]
R0, NSEG, SIDES = float(os.environ.get('HORN_R', '0.035')), 10, 8
PX = (1935, 1991, 98, 246); ATL = 2048                 # a clean ivory window (64 x 160 px, std < 6) outside every mask


def bez(t):
    p = [np.array(c) for c in CTRL]
    return ((1 - t) ** 3) * p[0] + 3 * ((1 - t) ** 2) * t * p[1] + 3 * (1 - t) * t * t * p[2] + t ** 3 * p[3]


if 'Horns' in [m.name for m in me.materials]:
    pass
nv0 = len(me.vertices)
bm = bmesh.new(); bm.from_mesh(me)
uvl = bm.loops.layers.uv.active
pa = bm.verts.layers.int.get('piece'); ga = bm.verts.layers.int.get('garment')
print('CUSTOMN before', me.has_custom_normals)
oc = bm.verts.layers.float_vector.get('orig_co')
dl = bm.verts.layers.deform.verify()
head_gi = body.vertex_groups['mixamorig:Head'].index
new_faces = []
for side, piece in ((1, 35), (-1, 36)):
    rings = []
    for k in range(NSEG + 1):
        t = k / NSEG
        c = bez(t); c[0] *= side
        d = bez(min(1, t + 0.01)) - bez(max(0, t - 0.01)); d[0] *= side; d /= np.linalg.norm(d)
        if k == 0:
            c = c - d * 0.015
        ref = np.array([0, -1.0, 0]); u = ref - d * (ref @ d); u /= np.linalg.norm(u); w = np.cross(d, u)
        r = R0 * (1 - t) ** 0.9 + 0.002
        ring = []
        for s in range(SIDES):
            th = 2 * math.pi * s / SIDES
            p = c + (u * math.cos(th) * 0.85 + w * math.sin(th)) * r
            ring.append(bm.verts.new(Vector(p)))
        rings.append((ring, t))
    tipc = bez(1.0); tipc[0] *= side; d = tipc - bez(0.97) * np.array([side, 1, 1]); tip = bm.verts.new(Vector(tipc + d / np.linalg.norm(d) * 0.012))
    allv = [v for ring, _ in rings for v in ring] + [tip]
    for v in allv:
        v[pa] = piece
        if ga is not None: v[ga] = 3
        v[oc] = v.co.copy(); v[dl][head_gi] = 1.0
    def uv(t, s):
        x = PX[0] + (PX[1] - PX[0]) * (s / SIDES); y = PX[2] + (PX[3] - PX[2]) * t
        return (x / ATL, 1 - y / ATL)
    for k in range(NSEG):
        (r0, t0), (r1, t1) = rings[k], rings[k + 1]
        for s in range(SIDES):
            s2 = (s + 1) % SIDES
            f = bm.faces.new((r0[s], r0[s2], r1[s2], r1[s])); new_faces.append(f)
            for l, (tt, ss) in zip(f.loops, ((t0, s), (t0, s + 1), (t1, s + 1), (t1, s))):
                l[uvl].uv = uv(tt, ss)
    for s in range(SIDES):
        s2 = (s + 1) % SIDES
        f = bm.faces.new((rings[-1][0][s], rings[-1][0][s2], tip)); new_faces.append(f)
        for l, (tt, ss) in zip(f.loops, ((1, s), (1, s + 1), (1, s + 0.5))):
            l[uvl].uv = uv(tt, ss)
    f = bm.faces.new(list(reversed(rings[0][0]))); new_faces.append(f)
    for l in f.loops: l[uvl].uv = uv(0, 0)
bmesh.ops.recalc_face_normals(bm, faces=new_faces)
for f in new_faces:
    f.material_index = 0; f.smooth = True
bmesh.ops.triangulate(bm, faces=new_faces, quad_method='SHORT_EDGE')
bm.to_mesh(me); bm.free()
print('CUSTOMN after', me.has_custom_normals)
print('HORNS added', len(me.vertices) - nv0, 'vertices; tris now', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
