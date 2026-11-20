"""Rounder dwarf face (user review r6, 2026-11-02: "the head itself isnt like anatomic? its like missing some stuff near
temples?"). Measured (`face_measure.py`, face skin half-width from the face centre, ours vs MM9 PeasantDF1a): temples
(z 0.44-0.46) 5.2-5.4 vs 6.2 cm, cheeks (z 0.40-0.42) 5.6 vs 6.4 cm. Positions only on the head's skin shell:
- sides of the head and temples: outward in x by TEMPLE (peak at z 0.45, eased out by z 0.38 and 0.52), weighted by
  how far round to the side the vertex is (nothing on the front of the face: y < -0.085 m, full from y -0.055 m) and by
  its distance from the face centre (nothing within 2 cm);
- cheeks: outward by CHEEK and forward by CHEEK / 2 at z 0.37-0.42, 3.5-6.5 cm from the centre, in front;
- the eyes, nose and mouth stay: weights fade to 0 within 2.4 cm of each eye centre and within 2.2 cm of the midline in
  front. A one-ring Laplacian pass over the moved region smooths the displacement field.
Args (Blender): <in blend> <out blend> [temple 0.009] [cheek 0.006]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
TEMPLE = float(a[2]) if len(a) > 2 else 0.009
CHEEK = float(a[3]) if len(a) > 3 else 0.006
EYES = [Vector((0.018, -0.092, 0.437)), Vector((-0.028, -0.092, 0.436))]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; M = body.matrix_world; Mi = M.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lk = bm.faces.layers.int['head']; lh = bm.faces.layers.int['hand']; lt = bm.faces.layers.int.get('twin')
comp = {}; k = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = k; st.append(o)
    k += 1
cnt = np.bincount(list(comp.values())); big = int(cnt.argmax())
shell = {v for f in bm.faces if f[lk] and not f[lh] and not (lt and f[lt]) for v in f.verts if comp[v] == big}


def ss(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


cx = float(np.median([(M @ v.co).x for v in shell]))
D = {}
for v in shell:
    p = M @ v.co; d = abs(p.x - cx); sgn = 1 if p.x >= cx else -1
    eye = min(ss(((p - e).length - 0.016) / 0.008) for e in EYES)
    mid = ss((d - 0.014) / 0.008) if p.y < -0.06 else 1.0
    zt = ss((p.z - 0.38) / 0.05) * ss((0.52 - p.z) / 0.05)
    side = ss((p.y + 0.085) / 0.03) * ss((0.06 - p.y) / 0.05)
    wt = zt * side * ss((d - 0.02) / 0.02) * eye
    zc = ss((p.z - 0.365) / 0.02) * ss((0.425 - p.z) / 0.02)
    wc = zc * ss((d - 0.035) / 0.01) * ss((0.065 - d) / 0.01) * (1.0 if p.y < -0.05 else 0.0) * eye * mid
    dv = Vector((sgn * (TEMPLE * wt + CHEEK * wc), -CHEEK * 0.5 * wc, 0))
    if dv.length > 1e-6:
        D[v] = dv
zone = set(D) | {e.other_vert(v) for v in D for e in v.link_edges if e.other_vert(v) in shell}
F = {v: D.get(v, Vector()) for v in zone}
for _ in range(2):
    F = {v: (F[v] * 0.5 + sum((F.get(e.other_vert(v), Vector()) for e in v.link_edges), Vector()) / max(len(v.link_edges), 1) * 0.5)
         if v in D else F[v] for v in zone}
for v, dv in F.items():
    if dv.length > 1e-7:
        v.co = Mi @ (M @ v.co + dv)
bm.to_mesh(me); me.update()
mx = max((dv.length for dv in F.values()), default=0)
print('FACEWIDEN', json.dumps({'moved': sum(1 for dv in F.values() if dv.length > 1e-5), 'max_mm': round(mx * 1000, 1), 'temple': TEMPLE, 'cheek': CHEEK}))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
