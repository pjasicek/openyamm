"""Textured frames of chosen clips from the textured master (Workbench texture colour), three-quarter front at
chest height (plus back and back three-quarter). Args: -- <out dir> <action>:<frame>,<frame>... [...]"""
import bpy, sys, math, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/m428_textured_master.blend'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.45, 0.45, 0.45)
sc.render.resolution_x, sc.render.resolution_y = 520, 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.0
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for spec in a[1:]:
    name, fs = spec.split(':'); act = bpy.data.actions[name]
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    for f in [int(x) for x in fs.split(',')]:
        sc.frame_set(f)
        for view, yaw in (('front', 0), ('tq', 35), ('back', 180), ('backtq', 145)):
            r = math.radians(yaw); cam.location = (math.sin(r) * 4, -math.cos(r) * 4, 0.95)
            cam.rotation_euler = (math.radians(90), 0, r)
            sc.render.filepath = f'{out}/{name}_{f:03d}_{view}.png'; bpy.ops.render.render(write_still=True)
