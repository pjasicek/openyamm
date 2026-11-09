"""Posed overlay: the weighted 'Body' (grey) from a rig blend driven by the MM9 rig of the source blend, with the MM9
meshes (red, x-ray), at clip frames. Args: <source blend> <rig blend> <outdir> <clip@frame,...> [view] [ortho]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, RIG, OUT, POSES = argv[:4]
VIEW = argv[4] if len(argv) > 4 else 'right'
ORTHO = float(argv[5]) if len(argv) > 5 else 1.6
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
with bpy.data.libraries.load(RIG) as (src, dst):
    dst.objects = ['Body']
body = dst.objects[0]
sc.collection.objects.link(body)
body.parent = arm
for m in body.modifiers:
    if m.type == 'ARMATURE':
        m.object = arm
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0.15, 0.15, 0.45)
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.85, 0.85, 0.85, 1)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(grey if o is body else red)
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
sh.show_xray = False
sc.render.resolution_x = sc.render.resolution_y = 384
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ORTHO; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'right': (-1, 0, 0.15), 'left': (1, 0, 0.15), 'front': (0, -1, 0.15), 'q34': (-1, -1.25, 0.55), 'top': (0, 0.0001, 1)}
os.makedirs(OUT, exist_ok=True)
for spec in POSES.split(','):
    name, frame = spec.split('@')
    act = bpy.data.actions[name]
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(float(frame)))
    bpy.context.view_layer.update()
    for mode, show_mm9 in (('ours', False), ('both', True)):
        for o in bpy.data.objects:
            if o.type == 'MESH' and o is not body:
                o.hide_render = not show_mm9
        c = Vector((0, 0, 0.2))
        d = Vector(dirs[VIEW]).normalized()
        cam.location = c + d * 10
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f'{name}_{int(float(frame)):03d}_{mode}.png')
        bpy.ops.render.render(write_still=True)
print('POSED', POSES)
