"""Dump the Body mesh of a blend for numpy analysis: positions, triangles (with polygon index), loop UVs per triangle,
weights (dense over bone names), piece/chain attributes. Args: <blend> <out npz> [object name]"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
name = argv[2] if len(argv) > 2 else 'Body'
ob = bpy.data.objects[name]
me = ob.data
me.calc_loop_triangles()
n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
T = np.array([t.vertices[:] for t in me.loop_triangles])
TP = np.array([t.polygon_index for t in me.loop_triangles])
uvl = me.uv_layers.active
TUV = np.array([[uvl.data[l].uv[:] for l in t.loops] for t in me.loop_triangles]) if uvl else np.zeros((len(T), 3, 2))
names = [g.name for g in ob.vertex_groups]
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
att = {}
for a in ('piece', 'chain'):
    if a in me.attributes:
        att[a] = np.array([d.value for d in me.attributes[a].data])
rig = ob.parent if ob.parent and ob.parent.type == 'ARMATURE' else next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
bones = {b.name: np.array(b.matrix_local) for b in rig.data.bones} if rig else {}
np.savez(argv[1], P=P, T=T, TP=TP, TUV=TUV, W=W, names=np.array(names), bone_names=np.array(list(bones)),
         bone_mats=np.array(list(bones.values())), **att)
print('DUMPED', n, len(T))
