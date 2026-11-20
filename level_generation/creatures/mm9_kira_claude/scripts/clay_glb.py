"""Clay views of every mesh in a GLB (diagnosis). Args: <glb> <out prefix> <view spec ...>  spec: name:dx,dy,dz:cx,cy,cz:size"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'RANDOM' if 'RANDOM' in a[1] else 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.05, 0.25)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for sp in a[2:]:
    n, d, c, z = sp.split(':')
    d = Vector([float(x) for x in d.split(',')]).normalized(); c = Vector([float(x) for x in c.split(',')])
    cd.ortho_scale = float(z); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
print('CLAY done')
