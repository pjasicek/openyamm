"""Skirt follows the legs a little (coordinator review 2026-11-02: in Death the thighs pass 5.6 cm through the front of the
skirt). Body vertices mostly weighted to the skirt chains (XCOM_skirt, x*) below ZTOP take a share k of the weights of the
nearest leg vertex (mostly Thigh/Calf weighted, not skirt): k = K x (1 - d / DMAX) for a leg surface within DMAX, more at
the front (x FRONT for y < 0, Blender MM9 frame, the creature faces -y). Weights only.
Args: <in blend> <out blend> [k 0.35] [dmax 0.10] [ztop -0.05] [front 1.0] [back 0.5]"""
import bpy, sys
import numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
K = float(a[2]) if len(a) > 2 else 0.35; DMAX = float(a[3]) if len(a) > 3 else 0.10
ZTOP = float(a[4]) if len(a) > 4 else -0.05; FRONT = float(a[5]) if len(a) > 5 else 1.0; BACK = float(a[6]) if len(a) > 6 else 0.5
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; mw = ob.matrix_world
names = {g.index: g.name for g in ob.vertex_groups}
def share(v, pred): return sum(g.weight for g in v.groups if pred(names[g.group]))
isskirt = lambda n: n.startswith('x') or n.startswith('XCOM')
import os
LEGS = os.environ.get('LEGS', 'Thigh,Calf').split(',')   # HOF2 (2026-11-04): LEGS=Thigh,Calf,Foot (the heel kicked through the dress)
isleg = lambda n: any(t in n for t in LEGS)
skirt = [v for v in me.vertices if share(v, isskirt) > 0.5 and (mw @ v.co).z < ZTOP]
legs = [v for v in me.vertices if share(v, isleg) > 0.6]
kd = KDTree(len(legs))
for i, v in enumerate(legs): kd.insert(mw @ v.co, i)
kd.balance()
n = 0
for v in skirt:
    p = mw @ v.co
    co, i, d = kd.find(p)
    if d > DMAX: continue
    k = K * (1 - d / DMAX) * (FRONT if p.y < 0 else BACK)
    if k <= 0.01: continue
    old = {g.group: g.weight for g in v.groups}
    leg = {g.group: g.weight for g in legs[i].groups}
    new = {g: w * (1 - k) for g, w in old.items()}
    for g, w in leg.items(): new[g] = new.get(g, 0.0) + w * k
    for g in list(old): ob.vertex_groups[g].remove([v.index])
    for g, w in new.items():
        if w > 1e-4: ob.vertex_groups[g].add([v.index], w, 'REPLACE')
    n += 1
print('SKIRT_LEG_BLEND skirt verts', len(skirt), 'blended', n)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
