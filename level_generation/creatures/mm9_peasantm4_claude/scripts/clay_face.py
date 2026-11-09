"""Clay close-ups of the face: front, 3/4 and profile, with a 1 cm grid overlay drawn afterwards. Args: blend out_prefix [cx cy cz]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
c = Vector([float(x) for x in a[2:5]]) if len(a) > 4 else Vector((-0.015, -0.05, 0.725))
sc = bpy.context.scene; o = bpy.data.objects['Body']
for p in o.data.polygons: p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
sh.single_color = (0.8, 0.78, 0.75); sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.3); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.16
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, d in (('front', Vector((0, -1, 0))), ('q34', Vector((-0.7, -1, 0.1))), ('profile', Vector((-1, 0, 0))), ('below', Vector((-0.3, -1, -0.6)))):
    cam.location = c + d.normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
