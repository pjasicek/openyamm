"""Clay close-ups of the head of a GLB or blend (Body object). Args: <glb|blend> <out prefix> [cx,cy,cz] [ortho]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
if a[0].endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=a[0])
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
c = Vector([float(x) for x in a[2].split(',')]) if len(a) > 2 else Vector((0, 0, 0.93))
ortho = float(a[3]) if len(a) > 3 else 0.5
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .75, .75); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'front': (0, -1, 0), 'q34': (-1, -1.2, .2), 'side': (1, 0, 0), 'below': (0, -1, -0.6)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
