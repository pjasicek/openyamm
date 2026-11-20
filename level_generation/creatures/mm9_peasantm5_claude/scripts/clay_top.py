import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
sc = bpy.context.scene; o = bpy.data.objects['Body']
for p in o.data.polygons: p.use_smooth = True
# colour hair shell part red via vertex colour: simpler — material per part not needed; use random object colour off
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
sh.single_color = (0.8, 0.78, 0.75); sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.3); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.24
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((-0.007, -0.03, 0.84))
for name, d in (('top', Vector((0, -0.3, 1))), ('fronttop', Vector((0, -1, 0.6))), ('q34top', Vector((-0.8, -0.8, 0.8)))):
    cam.location = c + d.normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
