"""Deformation check: every 2nd frame of every clip, distance from each deformed retopology vertex to the deformed
source surface (both skinned by the same rig). Small, stable distances mean the transferred weights follow the
source. Prints mean / 99th percentile / max per clip (mm)."""
import os
import bmesh
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = os.environ['REA_TAG']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'retopo_{TAG}.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Wyrm_Rig']
src = bpy.data.objects['Wyrm']
new = bpy.data.objects[f'Wyrm_{TAG}']
results = {}
for action in bpy.data.actions:
    rig.animation_data.action = action
    first, last = (int(f) for f in action.frame_range)
    dists = []
    for f in range(first, last + 1, 2):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        sb = bmesh.new(); sb.from_object(src, dg); sb.transform(src.matrix_world)
        tree = BVHTree.FromBMesh(sb)
        me = new.evaluated_get(dg).to_mesh()
        mw = new.matrix_world
        d = [tree.find_nearest(mw @ v.co)[3] for v in me.vertices]
        new.evaluated_get(dg).to_mesh_clear(); sb.free()
        dists.extend(x for x in d if x is not None)
    a = np.array(dists) * 1000.0
    results[action.name] = (round(float(a.mean()), 2), round(float(np.percentile(a, 99)), 2), round(float(a.max()), 2))
    print('DEFORM', action.name, 'mean/p99/max mm', results[action.name])
