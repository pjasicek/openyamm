"""Symmetry of the rig (rest bone heads, L vs mirrored R) and of a mesh (distance from each vertex mirrored in x to
the surface), per component. Usage: blender -b -P sym_probe.py -- <glb> <mesh node>"""
import bpy, sys, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
glb, node = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
worst = []
for b in rig.data.bones:
    if '_L_' in b.name:
        r = rig.data.bones.get(b.name.replace('_L_', '_R_'))
        if r:
            hl = rig.matrix_world @ b.head_local; hr = rig.matrix_world @ r.head_local
            worst.append(((hl - Vector((-hr.x, hr.y, hr.z))).length * 1000, b.name))
worst.sort(reverse=True); print('RIG worst mm', [(round(d, 1), n) for d, n in worst[:5]])
c = [b for b in rig.data.bones if '_L_' not in b.name and '_R_' not in b.name]
print('RIG centre x mm', [(b.name, round((rig.matrix_world @ b.head_local).x * 1000, 1)) for b in c][:8])
o = bpy.data.objects[node]; bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
tree = BVHTree.FromBMesh(bm)
d = np.array([tree.find_nearest(Vector((-v.co.x, v.co.y, v.co.z)))[3] for v in bm.verts]) * 1000
print('MESH mirror distance mm: mean', round(d.mean(), 2), 'p90', round(np.percentile(d, 90), 2), 'p99', round(np.percentile(d, 99), 2), 'max', round(d.max(), 1))
xs = np.array([v.co.x for v in bm.verts]); print('MESH x range', round(xs.min(), 3), round(xs.max(), 3))
