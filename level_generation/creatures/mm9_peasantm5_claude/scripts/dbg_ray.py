import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data; mw = body.matrix_world
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
ha = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', ha)
gname = {g.index: g.name for g in body.vertex_groups}; BONES = {b.name for b in rig.data.bones}
dom = []
for v in me.vertices:
    w = {gname[g.group]: g.weight for g in v.groups if gname[g.group] in BONES and g.weight > 0}
    dom.append(max(w, key=w.get) if w else '')
tok = 'R'; arm = {f'Bip01 {tok} {k}' for k in ('UpperArm', 'Forearm', 'Hand')}
a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
L = np.linalg.norm(a1 - a0); axis = (a1 - a0) / L
onarm = np.array([d in arm for d in dom])
sf = [p for p in me.polygons if not ha[p.index] and onarm[list(p.vertices)].sum() >= 2]
bvh = BVHTree.FromPolygons([Vector(c) for c in CO], [list(p.vertices) for p in sf])
i = 3532
t = (CO[i] - a0) @ axis; p0 = a0 + t * axis; r = CO[i] - p0; rv = np.linalg.norm(r); rd = r / rv
print('DBG a0', a0.round(3), 'a1', a1.round(3), 't', round(t, 3), 'L', round(L, 3), 'rv', round(rv, 4), 'sleeve faces', len(sf))
print('DBG hit', bvh.ray_cast(Vector(p0), Vector(rd), 0.10))
print('DBG hit far', bvh.ray_cast(Vector(p0), Vector(rd), 1.0))
