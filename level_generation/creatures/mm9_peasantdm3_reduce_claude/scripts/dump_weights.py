"""Source vertex weights (work/source.blend Body, same vertex order as dump_mesh.py) -> work/src_weights.npz
(weights matrix, group names)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; gi = {g.index: g.name for g in src.vertex_groups if g.name != 'ReduceProtect'}
names = sorted(set(gi.values())); col = {n: k for k, n in enumerate(names)}
W = np.zeros((len(src.data.vertices), len(names)), np.float32)
for v in src.data.vertices:
    for g in v.groups:
        if g.group in gi:
            W[v.index, col[gi[g.group]]] = g.weight
np.savez(os.path.join(HERE, 'work', 'src_weights.npz'), weights=W, names=np.array(names))
print('WEIGHTS', W.shape)
