"""Claw tips the foot rule of rig_dillo.py missed (it skipped |x| < 0.10, where each front foot's inner claw sits):
heat weights left them on Spine, so they stretched to the floor when the body moved (thin spikes from the chin to the
floor in Attack/Walking). Every vertex below z LOW that is connected through vertices below LOW to a vertex wholly on
a foot bone (Hand_* / HindFoot_*), within RADIUS (xy) of that foot's centre, goes wholly on that foot bone (front feet
0.22 m; hind feet 0.13 m, since the belly skirt hangs low just ahead of them). Starts from rig_v2.blend's weights (same
vertices), so it can be rerun. Weights only (no vertex moves, so the UV layout and the paint stay valid). Edits
work/anim_base.blend in place."""
import bpy, os
import numpy as np
from collections import deque
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOW = 0.07
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v2.blend'))
src = bpy.data.objects['Dillo']
W0 = [[(src.vertex_groups[g.group].name, g.weight) for g in v.groups] for v in src.data.vertices]
co0 = np.array([v.co[:] for v in src.data.vertices])
path = os.path.join(HERE, 'work', 'anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=path)
ob = bpy.data.objects['Dillo']; me = ob.data
names = [g.name for g in ob.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
co = np.array([v.co[:] for v in me.vertices])
assert co.shape == co0.shape and np.abs(co - co0).max() < 1e-6, 'anim_base vertices differ from rig_v2'
for i, ws in enumerate(W0):
    for g in list(me.vertices[i].groups):
        ob.vertex_groups[g.group].remove([i])
    for n, w in ws:
        ob.vertex_groups[gi[n]].add([i], w, 'REPLACE')
nbr = [[] for _ in me.vertices]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
FOOT = {'Hand_L': (0.232, -0.89, 0.22), 'Hand_R': (-0.232, -0.89, 0.22), 'HindFoot_L': (0.288, -0.19, 0.13),
        'HindFoot_R': (-0.288, -0.19, 0.13)}


def dominant(i):
    gs = me.vertices[i].groups
    return max(((names[g.group], g.weight) for g in gs), key=lambda x: x[1]) if len(gs) else ('', 0)


changed = {}
for foot, (fx, fy, rad) in FOOT.items():
    seeds = [i for i in range(len(co)) if co[i, 2] < LOW and dominant(i) == (foot, 1.0)]
    seen = set(seeds); q = deque(seeds)
    while q:
        i = q.popleft()
        for j in nbr[i]:
            if j in seen or co[j, 2] >= LOW or np.hypot(co[j, 0] - fx, co[j, 1] - fy) > rad:
                continue
            seen.add(j); q.append(j)
    for i in seen:
        d = dominant(i)
        if d != (foot, 1.0):
            for g in list(me.vertices[i].groups):
                ob.vertex_groups[g.group].remove([i])
            ob.vertex_groups[gi[foot]].add([i], 1.0, 'REPLACE')
            changed[foot] = changed.get(foot, 0) + 1
print('FIXED claw vertices per foot', changed)
bpy.ops.wm.save_as_mainfile(filepath=path)
