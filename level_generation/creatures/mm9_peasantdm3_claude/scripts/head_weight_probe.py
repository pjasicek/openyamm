"""Rigid-head check (VARIANTS_BRIEF: the whole face, lips, chin, jaw, moves with the Head bone): head-shell vertices above
the neck base (rest z > 0.315, in front of y 0.03: face, beard, jaw) with any weight not on Bip01 Head; also the hair's
weight bands. Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = L.rest_coords(body); lab = L.loose_parts(body.data)
cand = np.where((co[:, 2] > 0.40) & (co[:, 2] < 0.47))[0]
shell = lab[cand[np.argmin(co[cand, 1])]]
vg = {g.index: g.name for g in body.vertex_groups}
bad = []
for i in np.where((lab == shell) & (co[:, 2] > 0.315) & (co[:, 1] < 0.03))[0]:
    ws = {vg[g.group]: g.weight for g in body.data.vertices[i].groups if g.weight > 1e-4}
    tot = sum(ws.values()); h = ws.get('Bip01 Head', 0) / max(tot, 1e-9)
    if h < 0.999:
        bad.append((round(float(co[i, 2]), 3), round(float(co[i, 1]), 3), round(h, 2)))
print('HEADW', json.dumps({'face_vertices_checked': int(((lab == shell) & (co[:, 2] > 0.315) & (co[:, 1] < 0.03)).sum()),
                           'not_rigid': len(bad), 'examples': sorted(bad)[:20]}))
