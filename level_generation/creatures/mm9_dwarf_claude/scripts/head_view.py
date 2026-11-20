"""Clay views of the head blend's objects. Args: <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.2, 0.22)
for k, o in enumerate(bpy.data.objects): o.color = [(.75, .65, .6, 1), (.6, .65, .75, 1), (.85, .8, .6, 1), (.9, .9, .9, 1)][k % 4]
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]) if len(a) > 2 else 0.5; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in (('front', (0, -1, 0)), ('q34', (-1, -1.2, 0.15)), ('left', (1, 0, 0)), ('back', (0, 1, 0)), ('under', (0, -0.5, -1))):
    d = Vector(d).normalized(); cam.location = d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
