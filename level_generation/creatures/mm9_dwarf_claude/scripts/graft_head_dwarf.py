"""Head-only Meshy parts on the body. Face (Meshy's face and beard), Helm, Horns, Eyes go in as parts 20, 21, 23, 22, at MM9's head box. Meshy's neck behind the beard went to shards in reduction, so it goes and a plain tube runs from inside the skull
into the chest (hidden by the helmet's shell and the beard). The shoulders' dome under the helmet is pressed down so that the shell's rim clears it. Args: <fit blend> <head blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
OFF = np.array([0.0, float(os.environ.get('HEAD_Y', -0.03)), float(os.environ.get('HEAD_Z', 0.487))])
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 20, 'Helm': 21, 'Horns': 23, 'Eyes': 22}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.faces.layers.int['part']
# the dome under the helmet
RIM = OFF[2] - 0.157 + 0.0                    # lowest point of the shell's back rim
cy = OFF[1] + 0.02
moved = 0
skin = {v for f in bm.faces if f[lay] == 1 for v in f.verts}
for v in skin:
    r = np.hypot(v.co.x, (v.co.y - cy) * 0.85)
    limit = RIM - 0.012 + max(0.0, r - 0.125) * 1.2
    if v.co.z > limit and r < 0.22:
        k = np.clip((0.22 - r) / 0.06, 0, 1); k = k * k * (3 - 2 * k)
        v.co.z = v.co.z * (1 - k) + limit * k; moved += 1
print('DOME moved', moved, 'rim', round(float(RIM), 3))
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co = v.co + Vector(OFF)
    if nm == 'Face':
        # the neck and the hidden back of the skull go (head-local y > y0, below the ear line)
        dead = [f for f in t.faces if (f.calc_center_median().y - OFF[1] > -0.015 and f.calc_center_median().z - OFF[2] < -0.05) or f.calc_center_median().y - OFF[1] > 0.05]
        bmesh.ops.delete(t, geom=dead, context='FACES')
        bmesh.ops.delete(t, geom=[v for v in t.verts if not v.link_faces], context='VERTS')
        for _ in range(2):
            seen = set()
            for e0 in [e for e in t.edges if e.is_boundary]:
                if e0 in seen: continue
                st = [e0]; seen.add(e0); cur = []
                while st:
                    x = st.pop(); cur.append(x)
                    for v in x.verts:
                        for y in v.link_edges:
                            if y.is_boundary and y not in seen: seen.add(y); st.append(y)
                q = np.array([v.co[:] for e in cur for v in e.verts])
                if len(cur) <= 8: bmesh.ops.holes_fill(t, edges=cur, sides=len(cur))
        print('FACE tris', len(t.faces))
    tl = t.faces.layers.int.new('part')
    for f in t.faces: f[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); bmesh.ops.triangulate(t, faces=[f for f in t.faces if len(f.verts) > 3]); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
lay = bm.faces.layers.int['part']
# neck tube: rings, a cap inside the skull, open below in the chest
NR = 16
yc = OFF[1] + 0.035
Z = [OFF[2] - 0.02, OFF[2] - 0.07, OFF[2] - 0.12, OFF[2] - 0.17, OFF[2] - 0.22]
Rx = [0.05, 0.072, 0.078, 0.082, 0.085]; Ry = [0.05, 0.07, 0.074, 0.078, 0.08]
rings = [[bm.verts.new((np.cos(a) * rx, yc + np.sin(a) * ry, z)) for a in np.arange(NR) * 2 * np.pi / NR] for z, rx, ry in zip(Z, Rx, Ry)]
top = bm.verts.new((0, yc, Z[0] + 0.012))
new = []
for i in range(NR):
    k = (i + 1) % NR
    new.append(bm.faces.new((top, rings[0][i], rings[0][k])))
    for a, b in zip(rings[:-1], rings[1:]):
        new += [bm.faces.new((a[i], b[i], b[k])), bm.faces.new((a[i], b[k], a[k]))]
for f in new: f[lay] = 24; f.smooth = True
bmesh.ops.recalc_face_normals(bm, faces=new)
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o_ in list(bpy.data.objects):
    if o_.type == 'MESH' and o_ is not body: bpy.data.objects.remove(o_)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
