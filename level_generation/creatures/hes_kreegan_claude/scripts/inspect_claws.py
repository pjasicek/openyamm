import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
co = np.array([v.co[:] for v in me.vertices])
vm = np.zeros(len(co), int)
for p in me.polygons:
    for v in p.vertices: vm[v] = max(vm[v], p.material_index)
# cluster claw-material verts by connectivity through claw faces
import collections
adj = collections.defaultdict(set)
for p in me.polygons:
    if p.material_index == 3:
        vs = list(p.vertices)
        for a in vs:
            for b in vs: adj[a].add(b)
# also weld by position
key = {tuple(np.round(co[i] / 1e-5).astype(int)): i for i in adj}
seen = set(); groups = []
pos = collections.defaultdict(list)
for i in adj: pos[tuple(np.round(co[i] / 1e-5).astype(int))].append(i)
for i in adj:
    for j in pos[tuple(np.round(co[i] / 1e-5).astype(int))]: adj[i].add(j)
for i in adj:
    if i in seen: continue
    st = [i]; g = []
    seen.add(i)
    while st:
        x = st.pop(); g.append(x)
        for y in adj[x]:
            if y not in seen: seen.add(y); st.append(y)
    groups.append(g)
for g in sorted(groups, key=lambda g: -len(g)):
    c = co[g]
    bones = collections.Counter()
    for i in g:
        v = me.vertices[i]
        if v.groups: bones[body.vertex_groups[max(v.groups, key=lambda x: x.weight).group].name] += 1
    print('CLAW', len(g), np.round(c.mean(0), 3).tolist(), 'len', round(float(np.linalg.norm(c.max(0) - c.min(0))), 3), bones.most_common(1))
