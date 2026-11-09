"""Dump the rest-pose source mesh for texture-aware decimation: work/mesh_in.npz (vertices, triangles, wedge UVs with
each material shifted by +2*index in u, protect flag (unused here, 0), material per face, per-vertex weight sums of the
hand/finger bones and the dominant bone name)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']
me = src.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
names = [g.name for g in src.vertex_groups]
handidx = {g.index for g in src.vertex_groups if any(k in g.name for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))}
hw = np.array([sum(g.weight for g in v.groups if g.group in handidx) for v in me.vertices])
dom = np.array([max(v.groups, key=lambda g: g.weight).group if len(v.groups) else -1 for v in me.vertices])
tris = me.loop_triangles
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
np.savez(os.path.join(HERE, 'work', 'mesh_in.npz'),
         verts=np.array([v.co[:] for v in me.vertices]),
         faces=np.array([t.vertices[:] for t in tris], np.int32),
         wuv=np.array([[uv[l].uv[0] + 2.0 * t.material_index, uv[l].uv[1]] for t in tris for l in t.loops]),
         protect=np.zeros(len(tris)), mat=np.array([t.material_index for t in tris]),
         handw=hw, dom=dom, names=np.array(names), W=W)
print('DUMPED', len(me.vertices), len(tris))
