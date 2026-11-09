"""Clay views of a blend's Body. Args: <blend> <out prefix> <view spec ...>  spec: name:dx,dy,dz:cx,cy,cz:size"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and o.name != 'Body': o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.05, 0.25)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for sp in a[2:]:
    n, d, c, z = sp.split(':')
    d = Vector([float(x) for x in d.split(',')]).normalized(); c = Vector([float(x) for x in c.split(',')])
    cd.ortho_scale = float(z); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
