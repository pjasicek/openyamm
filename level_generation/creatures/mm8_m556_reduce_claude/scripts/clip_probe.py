"""Per-key probe of one clip of a viewer GLB (body with sword and shield baked in): thorax and Hand_L world positions,
the lowest body vertex, the lowest prop vertex, and the smallest distance from a sword-blade vertex to the body
surface away from the left arm (blade-through-body check). Usage: blender -b -P clip_probe.py -- <glb> <clip> <out.npz>"""
import os, sys, bpy
import numpy as np
from mathutils.bvhtree import BVHTree
glb, clip, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = bpy.data.objects['Wasp']; sword = bpy.data.objects['SwordMesh']; shield = bpy.data.objects['ShieldMesh']
names = [g.name for g in body.vertex_groups]
arm = {names.index(n) for n in names if n.endswith('_L') and any(n.startswith(p) for p in ('Hand', 'Claw', 'ForeArm', 'UpperArm'))}
not_arm = [v.index for v in body.data.vertices if not v.groups or max(v.groups, key=lambda g: g.weight).group not in arm]
act = bpy.data.actions[clip]; rig.animation_data.action = act
fps = sc.render.fps / sc.render.fps_base; f0, f1 = act.frame_range; n = int(round((f1 - f0) / fps * 48)) + 1
rows = []
for i in range(n):
    fr = f0 + i / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr)); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); mw = body.matrix_world
    bv = np.array([(mw @ v.co)[:] for v in ev.data.vertices])
    keep = set(not_arm); faces = [p.vertices[:] for p in ev.data.polygons if all(x in keep for x in p.vertices)]
    tree = BVHTree.FromPolygons([tuple(x) for x in bv], faces)
    sw = np.array([(sword.matrix_world @ v.co)[:] for v in sword.evaluated_get(dg).data.vertices])
    sh = np.array([(shield.matrix_world @ v.co)[:] for v in shield.evaluated_get(dg).data.vertices])
    dmin = min(tree.find_nearest(p)[3] for p in sw)
    th = rig.matrix_world @ rig.pose.bones['Thorax'].head; hd = rig.matrix_world @ rig.pose.bones['Hand_L'].head
    rows.append([th.z, bv[:, 2].min(), min(sw[:, 2].min(), sh[:, 2].min()), dmin, hd.x, hd.y, hd.z])
np.savez(out, rows=np.array(rows))
print('PROBE', clip, n, 'min body z', round(float(np.array(rows)[:, 1].min()), 4), 'min prop z', round(float(np.array(rows)[:, 2].min()), 4),
      'min blade-body mm', round(float(np.array(rows)[:, 3].min() * 1000), 1))
