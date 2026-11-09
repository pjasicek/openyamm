"""Render the MM9 source mesh coloured by dominant bone for the listed bones (others grey), views left/front,
bind pose or ACTION@FRAME. Args: <source blend> <out prefix> <bones comma> [action@frame]"""
import bpy, sys, colorsys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
OUT, BONES = argv[1], argv[2].split(',')
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
if len(argv) > 3:
    a, f = argv[3].split('@')
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[a]
    try:
        arm.animation_data.action_slot = bpy.data.actions[a].slots[0]
    except Exception:
        pass
    sc.frame_set(int(f))
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    me = o.data
    col = me.color_attributes.new('vc', 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        n = o.vertex_groups[g.group].name
        rgb = colorsys.hsv_to_rgb(BONES.index(n) / len(BONES), 0.85, 0.95) if n in BONES else (0.5, 0.5, 0.5)
        col.data[v.index].color = (*rgb, 1)
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 1.6
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, -0.1, 1.6))
for name, d in {'left': Vector((1, 0, 0)), 'front': Vector((0, -1, 0))}.items():
    cam.location = c + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}_{name}.png'
    bpy.ops.render.render(write_still=True)
for i, b in enumerate(BONES):
    print('COLOR', b, [round(x, 2) for x in colorsys.hsv_to_rgb(i / len(BONES), 0.85, 0.95)])
