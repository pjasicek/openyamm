"""Dump the rest-pose source mesh for texture-aware decimation: work/mesh_in.npz (vertices, triangles, wedge UVs with
the head material shifted by +2 in u, protection flag per face = Head/Jaw dominated)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects[os.environ.get('REA_MESH', 'Body')]
me = src.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
prot_idx = {g.index for g in src.vertex_groups if any(p in g.name for p in os.environ.get('REA_PROTECT', 'Head,Jaw').split(','))}
pw = np.array([sum(g.weight for g in v.groups if g.group in prot_idx) for v in me.vertices])
tris = me.loop_triangles
np.savez(os.path.join(HERE, 'work', 'mesh_in.npz'),
         verts=np.array([v.co[:] for v in me.vertices]),
         faces=np.array([t.vertices[:] for t in tris], np.int32),
         wuv=np.array([[uv[l].uv[0] + 2.0 * t.material_index, uv[l].uv[1]] for t in tris for l in t.loops]),
         protect=np.array([float(pw[list(t.vertices)].mean() > .5) for t in tris]))
print('DUMPED', len(me.vertices), len(tris))

# Keep small pieces (teeth and pores) and the sole contact surface; reduce dense head/fingers gently.
parent = list(range(len(me.vertices)))
def root(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for edge in me.edges:
    a, b = (root(i) for i in edge.vertices)
    parent[a] = b
pieces = np.array([root(t.vertices[0]) for t in tris])
counts = np.bincount(pieces, minlength=len(parent))
finger_idx = {g.index for g in src.vertex_groups if 'Finger' in g.name}
fw = np.array([sum(g.weight for g in v.groups if g.group in finger_idx) for v in me.vertices])
kept = np.array([t.material_index == 2 or counts[pieces[i]] <= 80 or any(me.vertices[v].co.z < .02 for v in t.vertices)
                 for i, t in enumerate(tris)])
groups = np.array([1 if t.material_index == 1 else 2 if any(fw[i] > .3 for i in t.vertices) else 0 for t in tris])
np.save(os.path.join(HERE, 'work', 'keep.npy'), kept)
np.save(os.path.join(HERE, 'work', 'groups.npy'), groups)
print('KEPT', int(kept.sum()), 'GROUPS', {g: int(((groups == g) & ~kept).sum()) for g in (0, 1, 2)}, flush=True)
import sys
sys.stdout.flush();sys.stderr.flush();os._exit(0)
