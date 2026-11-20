"""Rest positions, head-set flag (right half of the atlas), piece id and full weights per vertex of work/source.blend
-> work/vweights.npz (W: vertices x groups, names)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
b = bpy.data.objects['Body']; me = b.data
names = [g.name for g in b.vertex_groups]
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
uv = me.uv_layers.active.data; head = np.zeros(len(me.vertices), bool)
for l in me.loops:
    if uv[l.index].uv[0] > 1056 / 2080:
        head[l.vertex_index] = True
np.savez(os.path.join(HERE, 'work', 'vweights.npz'), co=np.array([v.co[:] for v in me.vertices]), W=W,
         names=np.array(names), head=head, faces=np.array([p.vertices[:] for p in me.polygons if len(p.vertices) == 3]))
print('VW', W.shape, head.sum())
