"""Render one vertex group's weight on 'Body' as colour (red = 1). Args: <blend> <outdir> <group> [centre x,y,z] [ortho]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
o = bpy.data.objects[os.environ.get('OBJ', 'Body')]
for x in bpy.data.objects:
    if x.type == 'MESH' and x != o:
        x.hide_render = True
gi = o.vertex_groups[argv[2]].index
me = o.data
if 'wv' in me.color_attributes:
    me.color_attributes.remove(me.color_attributes['wv'])
col = me.color_attributes.new('wv', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    w = next((g.weight for g in v.groups if g.group == gi), 0.0)
    col.data[v.index].color = (0.2 + 0.8 * w, 0.2 + 0.6 * (1 - w), 0.2 + 0.6 * (1 - w), 1)
me.color_attributes.active_color = col
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(argv[4]) if len(argv) > 4 else 0.3
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in argv[3].split(',')]) if len(argv) > 3 else Vector((0, -0.62, 0.8))
for n, d in {'front': (0, -1, 0), 'left': (1, 0, 0), 'below': (0, -0.3, -1), 'q34': (-1, -1.25, 0.2)}.items():
    cam.location = c + Vector(d).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'w_{argv[2]}_{n}.png'); bpy.ops.render.render(write_still=True)
