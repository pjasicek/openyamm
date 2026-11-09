"""Render the rigged 'Body' coloured by dominant bone for the listed bones (others grey), views left/front, bind pose
or ACTION@FRAME. Args: <blend> <out prefix> <bones comma> [action@frame] [cx,cy,cz] [ortho]"""
import bpy, sys, colorsys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
OUT, BONES = argv[1], argv[2].split(',')
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if len(argv) > 3 and argv[3] != '-':
    a, f = argv[3].split('@')
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[a]
    try:
        arm.animation_data.action_slot = bpy.data.actions[a].slots[0]
    except Exception:
        pass
    sc.frame_set(int(f))
else:
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
c = Vector(tuple(float(x) for x in argv[4].split(','))) if len(argv) > 4 else Vector((0, -0.1, 1.6))
ortho = float(argv[5]) if len(argv) > 5 else 1.6
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    me = o.data
    col = me.color_attributes.new('wc', 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        g = max(v.groups, key=lambda g: g.weight) if v.groups else None
        n = o.vertex_groups[g.group].name if g else ''
        rgb = colorsys.hsv_to_rgb(BONES.index(n) / len(BONES), 0.85, 0.95) if n in BONES else (0.5, 0.5, 0.5)
        col.data[v.index].color = (*rgb, 1)
    me.color_attributes.active_color = col
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, d in {'left': Vector((1, 0, 0)), 'front': Vector((0, -1, 0))}.items():
    cam.location = c + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}_{name}.png'
    bpy.ops.render.render(write_still=True)
