"""Render a clip at N evenly spaced times from front and side (and optionally three-quarter) with textures.
Args: out_prefix clip n [views comma list]. Writes <out_prefix>_<view>_<k>.png."""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
out, clip, n = args[0], args[1], int(args[2])
views = args[3].split(',') if len(args) > 3 else ['front', 'side']
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = 360; sc.render.resolution_y = 360
sc.display.shading.background_type = 'VIEWPORT'; sc.display.shading.background_color = (0.27, 0.29, 0.33)
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.data.materials:
            if m and m.use_nodes:
                t = next((x for x in m.node_tree.nodes if x.type == 'TEX_IMAGE'), None)
                if t: m.node_tree.nodes.active = t
rig = bpy.data.objects['Flying_Demon_Rig']
act = bpy.data.actions[clip]; rig.animation_data.action = act
f0, f1 = act.frame_range
cam = bpy.data.objects.new('cv', bpy.data.cameras.new('cv')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.2
LOC = {'front': (0, -6, 1.2), 'side': (6, 0, 1.2), 'q': (4.2, -4.2, 2.2), 'back': (0, 6, 1.2), 'left': (-6, 0, 1.2)}
for k in range(n):
    f = f0 + (f1 - f0) * k / max(n - 1, 1)
    sc.frame_set(int(f), subframe=f - int(f))
    for v in views:
        cam.location = LOC[v]; d = Vector((0, 0, 1.2)) - Vector(LOC[v]); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{v}_{k:02d}.png'; bpy.ops.render.render(write_still=True)
print('SHEET', clip, f0, f1)
