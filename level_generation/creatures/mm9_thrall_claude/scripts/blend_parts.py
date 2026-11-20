"""Clay views of all objects of a head blend. Args: <blend> <prefix> [scale]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.3, 0.3, 0.33); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]) if len(a) > 2 else 0.5; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cc = Vector([float(x) for x in a[3].split(',')]) if len(a) > 3 else Vector((0, 0, 0))
for v, d in {'q34': (-1.0, -1.25, 0.2), 'front': (0, -1, 0.0), 'left': (1, 0, 0.0), 'back': (0, 1, 0.0), 'under': (0.3, -0.3, -1)}.items():
    d = Vector(d).normalized(); cam.location = cc + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{v}.png'; bpy.ops.render.render(write_still=True)
