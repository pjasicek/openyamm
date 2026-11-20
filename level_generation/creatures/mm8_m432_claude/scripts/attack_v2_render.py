"""Workbench renders of a master clip (Attack v2 review): args <blend> <action> <out_dir> <view,...> <frame> ...
Views: front (party side, -Y), side (+X), q34. Writes <out_dir>/<action>_<frame>_<view>.png."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / args[0]))
action, out, views, frames = args[1], P / args[2], args[3].split(','), [float(x) for x in args[4:]]
out.mkdir(parents=True, exist_ok=True)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
rig.animation_data.action = bpy.data.actions[action]; rig.animation_data.action_slot = bpy.data.actions[action].slots[0]
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 520, 640; sc.render.film_transparent = False
sc.world = sc.world or bpy.data.worlds.new('W'); sc.display.shading.background_type = 'VIEWPORT'
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
import os
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('R_SCALE', '2.6'))
target = Vector(tuple(float(x) for x in os.environ.get('R_TARGET', '0,-0.2,0.95').split(',')))
focus = os.environ.get('R_BONE')
pos = {'front': Vector((0, -6, 1.1)), 'side': Vector((6, -0.2, 1.1)), 'q34': Vector((4.2, -4.2, 1.6)),
       'back': Vector((0, 6, 1.1))}
for f in frames:
    sc.frame_set(int(f), subframe=f % 1)
    if focus:
        target = rig.matrix_world @ rig.pose.bones[focus].head
    for v in views:
        cam.location = pos[v] - Vector((0, -0.2, 0.95)) + target
        d = target - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(out / f'{action}_{f:05.2f}_{v}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', len(frames) * len(views))
