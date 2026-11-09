"""Dump a rigged Dagrell blend (Body on MM9_Rig with action FitPose) to an npz for numpy analysis.

Args: <blend> <out.npz> [action=FitPose]
Arrays: rest (n,3) Body rest positions, fit (n,3) positions posed by the action at frame 0, tris (m,3), W (n,bones),
bones, parent index per bone, head/tail rest (armature space), matrix_local (bones,4,4), pose (bones,4,4) armature-space
pose matrices at frame 0 of the action, AW armature world matrix.
"""
import bpy, sys
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = argv[:2]
ACT = argv[2] if len(argv) > 2 else 'FitPose'
bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name)
bones = [b.name for b in rig.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
me = body.data
n = len(me.vertices)
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
W = np.zeros((n, len(bones)))
gname = {g.index: g.name for g in body.vertex_groups}
for v in me.vertices:
    for g in v.groups:
        if gname[g.group] in bidx:
            W[v.index, bidx[gname[g.group]]] = g.weight
rig.animation_data_create()
act = bpy.data.actions[ACT]
rig.animation_data.action = act
try:
    rig.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).to_mesh()
fit = np.array([tuple(body.matrix_world @ v.co) for v in ev.vertices])
body.evaluated_get(dg).to_mesh_clear()
par = np.array([bidx[b.parent.name] if b.parent else -1 for b in rig.data.bones])
head = np.array([tuple(b.head_local) for b in rig.data.bones])
tail = np.array([tuple(b.tail_local) for b in rig.data.bones])
ml = np.array([np.array(b.matrix_local) for b in rig.data.bones])
pose = np.array([np.array(rig.pose.bones[b].matrix) for b in bones])
np.savez(OUT, rest=rest, fit=fit, tris=tris, W=W, bones=np.array(bones), parent=par, head=head, tail=tail, ml=ml,
         pose=pose, AW=np.array(rig.matrix_world), bodyW=np.array(body.matrix_world))
print('DUMPED', n, len(tris), len(bones))
