"""Per-vertex dominant bone of work/source.blend Body -> work/groups.npz (names, dominant index, weight matrix)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data
names = [g.name for g in src.vertex_groups]
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
np.savez(os.path.join(HERE, 'work', 'groups.npz'), names=np.array(names), W=W)
print('GROUPS', len(names))
