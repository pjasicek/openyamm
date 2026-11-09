"""Rigid head (VARIANTS_BRIEF): the beard wedge (reshape_dm3.py) pulled DM1's under-chin vertices down, and they kept
DM1's Head/Neck blend (head_weight_probe.py: 46 face/beard vertices at Head 0.43-0.97). Head-shell vertices above the
neck base (rest z > 0.315) in front of y -0.01 become 100 % Bip01 Head; the neck sides behind keep their blend.
Weights only. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = L.rest_coords(body); lab = L.loose_parts(body.data)
cand = np.where((co[:, 2] > 0.40) & (co[:, 2] < 0.47))[0]
shell = lab[cand[np.argmin(co[cand, 1])]]
H = body.vertex_groups['Bip01 Head']
n = 0
for i in np.where((lab == shell) & (co[:, 2] > 0.315) & (co[:, 1] < -0.01))[0]:
    v = body.data.vertices[int(i)]
    if any(g.group != H.index and g.weight > 1e-4 for g in v.groups):
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([int(i)])
        H.add([int(i)], 1.0, 'REPLACE'); n += 1
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('RIGIDBEARD', json.dumps({'vertices_made_rigid': n}))
