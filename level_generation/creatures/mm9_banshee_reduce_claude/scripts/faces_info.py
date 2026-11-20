"""work/source.blend -> work/faces_info.npz: per rest-pose triangle its material, vertex ids, dominant bone name per
vertex, positions; plus the vertex group names. Used to build keep/group masks in numpy."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
names = [g.name for g in o.vertex_groups]
dom = np.array([max(v.groups, key=lambda g: g.weight).group if len(v.groups) else -1 for v in me.vertices])
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
tris = me.loop_triangles
np.savez(os.path.join(HERE, 'work', 'faces_info.npz'), verts=np.array([v.co[:] for v in me.vertices]),
         faces=np.array([t.vertices[:] for t in tris], np.int32), mat=np.array([t.material_index for t in tris]),
         dom=dom, names=np.array(names), W=W, mats=np.array([m.name for m in me.materials]))
print('INFO', len(tris), np.bincount([t.material_index for t in tris]).tolist())
