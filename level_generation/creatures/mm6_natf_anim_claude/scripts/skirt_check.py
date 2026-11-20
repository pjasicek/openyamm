"""Skirt/leg intersection over every clip. Skirt = vertices driven by the cage in the installed model (same set in the
re-skinned one, found by rest position); legs = thigh/calf/foot-dominated vertices outside it.
(a) skirt panel vertices inside a leg (signed distance to the posed leg surface < -TOL);
(b) thigh vertices (rest z 0.62-0.88, under the skirt) outside the skirt panel (signed distance along the skirt's
    outward normal > TOL), i.e. leg visible through the cloth.
Usage: blender -b -P skirt_check.py -- <installed glb> <glb or blend to check> [step frames]"""
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
ref, path = a[0], a[1]; STEP = int(a[2]) if len(a) > 2 else 2; TOL = 0.003
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(ref))
rb = bpy.data.objects['Natf']; g = {x.index: x.name for x in rb.vertex_groups}
rco = np.array([v.co[:] for v in rb.data.vertices])
rcage = np.array([sum(x.weight for x in v.groups if g[x.group].startswith('Skirt_')) for v in rb.data.vertices])
skirt_keys = {tuple(np.round(c, 5)) for c in rco[rcage > 0.5]}
if path.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path)); body = bpy.data.objects['Body']
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
    body = bpy.data.objects['Natf']
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_viewport = True
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
g = {x.index: x.name for x in body.vertex_groups}
co = np.array([v.co[:] for v in body.data.vertices])
# rest positions before any reshape: match the reference skirt set by the reference's rest coordinates is not possible
# after a push, so use topology: same vertex order as the reference (one glTF export -> import)
assert len(co) == len(rco)
skirt = rcage > 0.5
legw = np.array([sum(x.weight for x in v.groups if any(t in g[x.group] for t in ('Thigh', 'Calf', 'Foot', 'Toe')))
                 for v in body.data.vertices])
# legs plus the body's own hip/buttock skin under the skirt (pieces excluded: at most 120 vertices per welded part)
key = {}
weld = np.array([key.setdefault(tuple(np.round(c, 6)), i) for i, c in enumerate(rco)])
par = np.arange(len(rco))
def find(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for p in body.data.polygons:
    vs = [weld[i] for i in p.vertices]
    for x in vs[1:]:
        ra, rb = find(vs[0]), find(x)
        if ra != rb: par[ra] = rb
root = np.array([find(weld[i]) for i in range(len(rco))]); big = np.bincount(root, minlength=len(rco))[root] > 120
leg = (rcage == 0) & big & (rco[:, 2] < 0.95)
thigh = leg & (rco[:, 2] > 0.62) & (rco[:, 2] < 0.90)
leg_faces = [p.index for p in body.data.polygons if all(leg[i] for i in p.vertices)]
skirt_faces = [p.index for p in body.data.polygons if all(skirt[i] for i in p.vertices)]
dg = bpy.context.evaluated_depsgraph_get()
print('CHECK', path, 'skirt', int(skirt.sum()), 'thigh', int(thigh.sum()))
for act in sorted(bpy.data.actions, key=lambda x: x.name):
    if act.name.endswith('_codex'):
        continue
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    wa = wb = 0.0; na = nb = 0; at_a = at_b = None; va = vb = None
    for f in range(f0, f1 + 1, STEP):
        sc.frame_set(f)
        ev = body.evaluated_get(dg); m = ev.to_mesh()
        pc = np.array([v.co[:] for v in m.vertices])
        lt = BVHTree.FromPolygons([Vector(c) for c in pc], [tuple(m.polygons[i].vertices) for i in leg_faces])
        st = BVHTree.FromPolygons([Vector(c) for c in pc], [tuple(m.polygons[i].vertices) for i in skirt_faces])
        ev.to_mesh_clear()
        cnt = 0
        for i in np.where(skirt)[0]:
            q, n, _, _ = lt.find_nearest(Vector(pc[i]), 0.05)
            if q is not None:
                d = (Vector(pc[i]) - q).dot(n)
                if d < -TOL:
                    cnt += 1
                    if -d > wa: wa, at_a, va = -d, f, i
        na = max(na, cnt); cnt = 0
        for i in np.where(thigh)[0]:
            q, n, _, _ = st.find_nearest(Vector(pc[i]), 0.05)
            if q is not None:
                d = (Vector(pc[i]) - q).dot(n)
                if d > TOL:
                    cnt += 1
                    if d > wb: wb, at_b, vb = d, f, i
        nb = max(nb, cnt)
    print(f'  {act.name:10s} skirt-in-leg max {wa * 1000:5.1f} mm (frame {at_a}) worst-frame count {na:4d} | '
          f'thigh-out-of-skirt max {wb * 1000:5.1f} mm (frame {at_b}) worst-frame count {nb:4d} | rest at '
          f'{None if va is None else rco[va].round(3).tolist()} / {None if vb is None else rco[vb].round(3).tolist()}')
