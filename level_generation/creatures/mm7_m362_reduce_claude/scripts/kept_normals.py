"""Restore the installed GLB's own normals on the reduced candidate (work/ladder.blend, in place). The import weld
merges glTF's normal-split vertices and the ladder shades every candidate smooth, so kept hard-surface pieces (skirt
strips, belt, studs) turned rounded. The normals come from the unwelded source GLB (LOD0), never from source.blend,
whose custom normals the weld scrambles. Per candidate corner at a source vertex: the source face's corner normal if
the candidate face is an unchanged source face, else the source vertex normal if all its source corners agree; new
vertices and split-vertex corners of new faces keep the computed smooth normal.
Usage: blender -b -P kept_normals.py -- <Cand_NN> <mesh_rNN.npz> <source.glb> <mesh node>"""
import os, sys, bpy
import numpy as np
from pathlib import Path
from mathutils import kdtree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
cand_name, npz, glb, node_name = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.open_mainfile(filepath=str(HERE / 'work' / 'ladder.blend'))
src_in = np.load(HERE / 'work' / 'mesh_in.npz'); sv, sf = src_in['verts'], src_in['faces']
D, B = read_glb(Path(glb)); node = next(n for n in D['nodes'] if n.get('name') == node_name)
prim = D['meshes'][node['mesh']]['primitives'][0]
acc = lambda i, dt: np.frombuffer(accessor_bytes(D, B, i), dt)
gp = acc(prim['attributes']['POSITION'], np.float32).reshape(-1, 3); gn = acc(prim['attributes']['NORMAL'], np.float32).reshape(-1, 3)
gi = acc(prim['indices'], {5123: np.uint16, 5125: np.uint32}[D['accessors'][prim['indices']]['componentType']]).reshape(-1, 3)
to_b = lambda a: np.stack([a[:, 0], -a[:, 2], a[:, 1]], 1)
gp, gn = to_b(gp), to_b(gn)
kd = kdtree.KDTree(len(sv))
for i, co in enumerate(sv):
    kd.insert(co, i)
kd.balance()
q = [kd.find(co) for co in gp]; wid = np.array([x[1] for x in q]); dist = np.array([x[2] for x in q])
assert dist.max() < 1e-5, dist.max()
face_n = {}   # sorted welded triple -> {welded vertex: normal}
vert_n = {}   # welded vertex -> list of corner normals
for t in gi:
    w = wid[t]
    face_n[tuple(sorted(w))] = {int(a): gn[k] for a, k in zip(w, t)}
    for a, k in zip(w, t):
        vert_n.setdefault(int(a), []).append(gn[k])
unique = {a: ns[0] for a, ns in vert_n.items() if np.abs(np.array(ns) - ns[0]).max() < 1e-3}
d = np.load(npz); sidx = d['src_index']
c = bpy.data.objects[cand_name]; me = c.data
assert len(me.vertices) == len(sidx)
me.calc_loop_triangles() if hasattr(me, 'calc_loop_triangles') else None
vn = np.array([v.normal[:] for v in me.vertices])
loops = np.zeros((len(me.loops), 3)); n_face = n_vert = n_new = 0
for p in me.polygons:
    vs = [int(sidx[me.loops[li].vertex_index]) for li in p.loop_indices]
    fn = face_n.get(tuple(sorted(vs))) if min(vs) >= 0 else None
    for li, s in zip(p.loop_indices, vs):
        vi = me.loops[li].vertex_index
        if fn is not None:
            loops[li] = fn[s]; n_face += 1
        elif s >= 0 and s in unique:
            loops[li] = unique[s]; n_vert += 1
        else:
            loops[li] = vn[vi]; n_new += 1
loops /= np.linalg.norm(loops, axis=1, keepdims=True) + 1e-12
me.normals_split_custom_set([tuple(x) for x in loops])
print('KEPTNORMALS corners from source faces', n_face, 'from smooth source vertices', n_vert, 'computed', n_new,
      'GLB triangles', len(gi), 'max weld dist', float(dist.max()))
bpy.ops.wm.save_mainfile(filepath=str(HERE / 'work' / 'ladder.blend'))
