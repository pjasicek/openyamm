"""Dump a posed body (and the joined axe, piece 1000) for the silhouette gate (model_gate.py): world vertex positions at
one clip frame, triangles, per-vertex piece/garment and the dominant-bone class (0 body, 1 arm: clavicle excluded,
upper arm/forearm/hand/fingers/twist; 2 head: B_Head), plus posed joint heads.
Args: -- <blend> <clip|rest> <frame> <out npz>"""
import bpy, sys, os
import numpy as np
blend, clip, frame, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create()
if clip == 'rest':
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
else:
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    if hasattr(rig.animation_data, 'action_slot') and act.slots:
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(float(frame)))
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(deps); me = ev.to_mesh()
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices], np.float64)
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles], np.int32)
ev.to_mesh_clear()
src = body.data
rest = np.array([tuple(body.matrix_world @ v.co) for v in src.vertices], np.float64)
n = len(src.vertices)
def attr(name):
    a = np.zeros(n, np.int32)
    if name in src.attributes:
        src.attributes[name].data.foreach_get('value', a)
    return a
piece, garment = attr('piece'), attr('garment')
names = [g.name for g in body.vertex_groups]
ARM = ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
cls = np.zeros(n, np.int32)
for v in src.vertices:
    best, bw = None, 0.0
    arm = head = 0.0
    for e in v.groups:
        nm = names[e.group]
        if any(k in nm for k in ARM) and 'Clavicle' not in nm:
            arm += e.weight
        if nm == 'B_Head':
            head += e.weight
    cls[v.index] = 1 if arm > 0.5 else (2 if head > 0.5 else 0)
joints = {pb.name: tuple(rig.matrix_world @ pb.head) for pb in rig.pose.bones}
np.savez(out, co=co, rest=rest, tris=tris, piece=piece, garment=garment, cls=cls,
         joint_names=np.array(list(joints)), joint_co=np.array(list(joints.values())))
print('DUMP', clip, frame, 'verts', n, 'tris', len(tris), 'arm verts', int((cls == 1).sum()), 'head verts', int((cls == 2).sum()))
