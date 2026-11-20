"""Exploration: Sapling skeleton + leaves with parameter overrides (JSON arg), workbench silhouette render."""
import bpy, sys, json, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
params = json.loads(args[0]); out = args[1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
base = dict(do_update=True, bevel=True, showLeaves=True, useArm=False, prune=False)
base.update(params)
r = bpy.ops.curve.tree_add(**base)
tree = bpy.data.objects['tree']; leaves = bpy.data.objects.get('leaves')
dg = bpy.context.evaluated_depsgraph_get()
pts = [tree.matrix_world @ Vector(c) for c in tree.bound_box]
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
if leaves:
    lp = [leaves.matrix_world @ v.co for v in leaves.data.vertices]
    llo = [min(p[i] for p in lp) for i in range(3)]; lhi = [max(p[i] for p in lp) for i in range(3)]
    print('LEAVES', len(leaves.data.polygons), 'bounds', [round(x, 2) for x in llo], [round(x, 2) for x in lhi])
me = bpy.data.meshes.new_from_object(tree.evaluated_get(dg))
print('TREE tris', sum(len(p.vertices) - 2 for p in me.polygons), 'bounds', [round(x, 2) for x in lo], [round(x, 2) for x in hi])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'OBJECT'
tree.color = (0.35, 0.2, 0.1, 1)
if leaves: leaves.color = (0.1, 0.35, 0.12, 1)
sc.render.resolution_x = 400; sc.render.resolution_y = 450; sc.render.film_transparent = True
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; H = max(hi[2], 1) * 1.1; cam.data.ortho_scale = max(H, (hi[0]-lo[0])*1.25)
cam.location = (0, -30, H * 0.47); cam.rotation_euler = (math.pi / 2, 0, 0)
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
