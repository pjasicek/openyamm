"""har: the scarf strips and straps that Smart Topology fused onto the torso shell (P00) hang in front of the chest as
open sheets; inside tests against them flagged the rifle 12 cm 'inside' the chest. A torso vertex is an outer-layer
'strip' vertex when a ray from the body axis (pelvis x/y, the vertex's height) toward it crosses the torso shell before
reaching it (the shell itself is hit first only by the vertices of the closed surface), grown by one edge ring.
Writes the point attribute 'strip' (1/0); rifle_clear.py and gates.py leave strip faces out of their inside tests.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([v.co[:] for v in me.vertices]); pv = np.array([a.value for a in me.attributes['piece'].data])
gv = np.array([a.value for a in me.attributes['garment'].data])
tor = gv == 1
faces = [tuple(f.vertices) for f in me.polygons if all(tor[i] for i in f.vertices)]
tree = BVHTree.FromPolygons(co.tolist(), faces)
pel = rig.data.bones['B_Pelvis'].head_local; sp2 = rig.data.bones['B_Spine2'].head_local
arm = np.zeros(len(co), bool)
names = [g.name for g in body.vertex_groups]
armg = {i for i, n in enumerate(names) if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))}
for v in me.vertices:
    arm[v.index] = sum(e.weight for e in v.groups if e.group in armg) > 0.3
strip = np.zeros(len(co), bool)
for i in np.where(tor & ~arm)[0]:
    p = Vector(co[i]); ax = Vector((pel.x, (pel.y + sp2.y) / 2, p.z)); d = p - ax
    L = d.length
    if L < 0.03:
        continue
    d.normalize()
    loc, n, fi, dist = tree.ray_cast(ax, d, L - 0.006)
    strip[i] = loc is not None
grow = strip.copy()
for e in me.edges:
    a, b = e.vertices
    if strip[a] and tor[b] and not arm[b]:
        grow[b] = True
    if strip[b] and tor[a] and not arm[a]:
        grow[a] = True
at = me.attributes.get('strip') or me.attributes.new('strip', 'INT', 'POINT')
at.data.foreach_set('value', grow.astype(int).tolist())
print('STRIPS torso vertices', int(tor.sum()), 'outer-layer strips', int(strip.sum()), 'grown', int(grow.sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
