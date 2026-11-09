import bpy, sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stress_pose.py')).read().split('sc = bpy.context.scene')[0])
mesh = bpy.data.objects['Thief']; me = mesh.data
PARTS = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
vp = {}
for p in me.polygons:
    for v in p.vertices: vp.setdefault(v, set()).add(PARTS[part[p.index]])
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([tuple(mesh.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
R = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
G = {g.index: g.name for g in mesh.vertex_groups}
# local stretch: displacement relative to neighbours
d = np.linalg.norm(P - R, axis=1)
nb = {}
for e in me.edges:
    a, b = e.vertices; nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
rel = np.array([max((np.linalg.norm((P[i]-R[i])-(P[j]-R[j])) for j in nb.get(i, [i])), default=0) for i in range(len(R))])
for i in np.argsort(-rel)[:12]:
    print('SPIKE', i, vp.get(i), 'rest', R[i].round(3), 'rel', round(float(rel[i]), 3),
          sorted(((round(g.weight, 2), G[g.group]) for g in me.vertices[i].groups), reverse=True))
