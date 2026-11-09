"""Measure the cleric's hands in rest pose: per hand the faces dominated by the hand bone and their extent from the
wrist joint, and the staff axis and radius at the grip (input of hands_mpfb.py and fit_hands.py).
Run: blender -b work/rig_v4.blend -P scripts/hands_measure.py -- work/hands/measure.json"""
import bpy, bmesh, json, sys, numpy as np
from mathutils import Vector
rig = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; staff = bpy.data.objects['Staff']
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
me = mesh.evaluated_get(dg).to_mesh(); P = np.array([(mesh.matrix_world @ v.co)[:] for v in me.vertices])
names = {g.index: g.name for g in mesh.vertex_groups}
src = mesh.data
W = {}
for v in src.vertices:
    for g in v.groups:
        W.setdefault(names[g.group], np.zeros(len(src.vertices)))[v.index] = g.weight
parts = np.zeros(len(src.polygons), int)
if 'part' in src.attributes: src.attributes['part'].data.foreach_get('value', parts)
out = {}
for side in ('Left', 'Right'):
    hw = W.get(side + 'Hand', np.zeros(len(P)))
    fw = W.get(side + 'ForeArm', np.zeros(len(P)))
    head = rig.matrix_world @ rig.pose.bones[side + 'Hand'].head
    fa = rig.matrix_world @ rig.pose.bones[side + 'ForeArm'].head
    hv = np.where(hw > .5)[0]
    d = np.linalg.norm(P[hv] - np.array(head[:]), axis=1)
    tip = P[hv][np.argmax(d)]
    faces = [p.index for p in src.polygons if hw[list(p.vertices)].mean() > .5]
    fparts = np.bincount(parts[faces]) if faces else []
    out[side] = dict(wrist=list(head), elbow=list(fa), n_hand_verts=int(len(hv)), n_hand_faces=len(faces), max_from_wrist=float(d.max()),
                     tip=tip.tolist(), centroid=P[hv].mean(0).tolist(), bbox_min=P[hv].min(0).tolist(), bbox_max=P[hv].max(0).tolist(),
                     parts=[int(x) for x in np.nonzero(fparts)[0]] if len(fparts) else [], part_counts=[int(x) for x in fparts[np.nonzero(fparts)[0]]] if len(fparts) else [])
sm = staff.evaluated_get(dg).to_mesh(); S = np.array([(staff.matrix_world @ v.co)[:] for v in sm.vertices])
sb = rig.matrix_world @ rig.pose.bones['Staff'].matrix
ax = (sb.to_3x3() @ Vector((0, 1, 0))).normalized(); o = sb.to_translation()
t = (S - np.array(o[:])) @ np.array(ax[:]); radial = S - np.array(o[:]) - np.outer(t, ax[:])
r = np.linalg.norm(radial, axis=1)
near = np.abs(t) < 0.06
out['staff'] = dict(origin=list(o), axis=list(ax), radius_near_grip=float(np.median(r[near])), t_range=[float(t.min()), float(t.max())],
                    radius_p90=float(np.percentile(r[near], 90)))
print('MEASURE', json.dumps(out))
json.dump(out, open(sys.argv[sys.argv.index('--') + 1], 'w'), indent=1)
