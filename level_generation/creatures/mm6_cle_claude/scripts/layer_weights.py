"""Layered-clothing weights for the cleric (work/rig_v1.blend in place, after cloak_rig.py).

1. Under the mantle: tunic vertices above MANTLE_Z that the collar/mantle shell covers (ray along the vertex normal
   meets the cloak shell within COVER_D) take the weights of the covering mantle point (barycentric), so the tunic
   stays under the mantle when the arms rise (stress_v1/v2: the tunic chest came through the mantle front; the
   per-vertex 'hid' flag missed most of it). The copy is then feathered FEATHER passes over the tunic's own edges
   into the uncovered tunic next to it.
2. Tunic skirt: below the belt the skirt (SkirtF/SkirtB and hidden tunic below BELT_Z) blends toward the thighs:
   factor SKIRT_MAX * smoothstep(BELT_Z .. KNEE_Z), split between LeftUpLeg/RightUpLeg by x (50/50 at the centre),
   so a stepping leg carries the skirt instead of passing through it.
At most 4 influences, renormalised."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
scene = bpy.context.scene
mesh = bpy.data.objects['Cleric']; me = mesh.data
PARTS = json.loads(scene['cle_parts'])
REG = json.loads(scene['cle_uv_regions'])
MANTLE_Z, COVER_D, FEATHER = 1.05, 0.06, 3
BELT_Z, KNEE_Z, SKIRT_MAX, SPLIT = 0.90, 0.50, 0.75, 0.08

part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
ureg = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['uv_region'].data.foreach_get('value', ureg)
hid = np.zeros(len(me.vertices)); me.attributes['hid'].data.foreach_get('value', hid)
names = [g.name for g in mesh.vertex_groups]
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
vparts = [set() for _ in me.vertices]
for p in me.polygons:
    for vi in p.vertices:
        vparts[vi].add(PARTS[part[p.index]])
co = [v.co.copy() for v in me.vertices]

# 1. under the mantle
cl = PARTS.index('Cloak')
cfaces = [p for p in me.polygons if part[p.index] == cl]
ctris = []
for p in cfaces:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1):
        ctris.append((vs[0], vs[k], vs[k + 1]))
tree = BVHTree.FromPolygons(co, ctris)
covered = 0
cov = set()
for v in me.vertices:
    i = v.index
    if vparts[i] != {'Torso'} or co[i].z < MANTLE_Z:
        continue
    loc, nrm, ti, d = tree.ray_cast(co[i] + v.normal * 1e-4, v.normal, COVER_D)
    if loc is None:
        continue
    a, b, c = (co[j] for j in ctris[ti])
    bc = barycentric_transform(loc, a, b, c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
    W[i] = sum(max(bc[k], 0.0) * W[ctris[ti][k]] for k in range(3))
    covered += 1
    cov.add(i)
tnbr = {}
for e in me.edges:
    a_, b_ = e.vertices
    if vparts[a_] == {'Torso'} and vparts[b_] == {'Torso'}:
        tnbr.setdefault(a_, set()).add(b_); tnbr.setdefault(b_, set()).add(a_)
ring = set(cov)
for _ in range(FEATHER):                               # uncovered tunic next to the copy: average with neighbours
    ring |= {j for i in ring for j in tnbr.get(i, ())}
    edge_band = [i for i in ring if i not in cov and co[i].z > MANTLE_Z - 0.08]
    nxt = W.copy()
    for i in edge_band:
        nxt[i] = 0.5 * W[i] + 0.5 * W[list(tnbr[i])].mean(0)
    W = nxt

# 2. tunic skirt toward the thighs
skirt = set()
for p in me.polygons:
    r = REG[ureg[p.index]]
    if part[p.index] == PARTS.index('Torso') and (r in ('SkirtF', 'SkirtB') or (r == 'Hidden' and p.center.z < BELT_Z)):
        skirt.update(p.vertices)
gi = {n: j for j, n in enumerate(names)}
for n in ('LeftUpLeg', 'RightUpLeg'):
    if n not in gi:
        mesh.vertex_groups.new(name=n); names.append(n); gi[n] = len(names) - 1
        W = np.hstack([W, np.zeros((len(W), 1))])


def smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


blended = 0
for i in skirt:
    if vparts[i] != {'Torso'}:
        continue
    f = SKIRT_MAX * smooth(BELT_Z - co[i].z, 0.0, BELT_Z - KNEE_Z)
    if f <= 0:
        continue
    left = smooth(co[i].x - 0.012, -SPLIT, SPLIT)
    W[i] *= 1 - f
    W[i, gi['LeftUpLeg']] += f * left
    W[i, gi['RightUpLeg']] += f * (1 - left)
    blended += 1

for v in me.vertices:
    i = v.index
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([i])
    w = W[i]
    top = np.argsort(-w)[:4]
    s = w[top].sum()
    for j in top:
        if w[j] > 1e-4:
            mesh.vertex_groups[names[j]].add([i], float(w[j] / s), 'REPLACE')
print('LAYERS', {'tunic under mantle': covered, 'skirt blended': blended})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
