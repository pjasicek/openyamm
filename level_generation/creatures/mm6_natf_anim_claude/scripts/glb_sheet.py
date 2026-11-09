"""Contact sheet of a runtime/viewer GLB's clips (workbench textured, three-quarter front from her right), N frames per
clip. Usage: blender -b -P glb_sheet.py -- <glb> <out.png> <N> <clip> [...]"""
import os, sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, N, clips = a[0], a[1], int(a[2]), a[3:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 60
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = sc.render.resolution_y = 380
w = bpy.data.worlds.new('W'); sc.world = w; w.color = (.42, .43, .45)
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2
c = Vector((0, 0, .95)); cam.location = c + Vector((-.75, -1, .25)).normalized() * 6
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
tiles = []
for cn in clips:
    act = bpy.data.actions[cn]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for k in range(N):
        f = f0 + (f1 - f0) * k / (N - 1); sc.frame_set(int(f), subframe=f - int(f))
        p = f'{out}_{cn}_{k}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); tiles.append(p)
print('TILES', len(tiles))
