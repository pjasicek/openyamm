"""How far the installed GLB's normals are from plain smooth normals of the same surface (welded by position):
angle per vertex corner, summarised per connected piece of the welded mesh (largest deviations first).
Usage: blender -b -P normal_dev.py -- <glb> <node>"""
import sys, bpy, numpy as np, collections
glb, node = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
o = bpy.data.objects[node]; me = o.data
co = np.array([v.co[:] for v in me.vertices])
cn = np.array([l.vector[:] for l in me.corner_normals])
# smooth normals per welded position: area-weighted face normals
key = {}; pid = np.array([key.setdefault(tuple(np.round(c, 5)), len(key)) for c in co])
fn = np.array([p.normal[:] for p in me.polygons]) * np.array([p.area for p in me.polygons])[:, None]
acc = np.zeros((len(key), 3))
for p in me.polygons:
    for vi in p.vertices:
        acc[pid[vi]] += fn[p.index]
acc /= np.linalg.norm(acc, axis=1, keepdims=True) + 1e-12
lv = np.array([l.vertex_index for l in me.loops])
ang = np.degrees(np.arccos(np.clip((cn * acc[pid[lv]]).sum(1), -1, 1)))
# pieces by welded connectivity
parent = list(range(len(key)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for e in me.edges:
    a, b = find(pid[e.vertices[0]]), find(pid[e.vertices[1]])
    if a != b: parent[a] = b
piece = np.array([find(pid[v]) for v in lv]); mat = np.zeros(len(lv), int)
for p in me.polygons:
    for li in p.loop_indices: mat[li] = p.material_index
out = []
for pc in np.unique(piece):
    m = piece == pc
    out.append((np.percentile(ang[m], 90), m.sum(), ang[m].mean(), np.round(co[lv[m]].mean(0), 3), int(mat[m][0])))
for r in sorted(out, key=lambda r: -r[1])[:25]:
    print(f'PIECE corners {r[1]:6d} mean {r[2]:5.1f} p90 {r[0]:5.1f} deg  ctr {r[3]} mat {r[4]}')
print('ALL mean', round(float(ang.mean()), 2), 'p90', round(float(np.percentile(ang, 90)), 2))
