"""Close clay views of a GLB at given blender-space centres. Args: glb outprefix size then name:cx,cy,cz:ortho ..."""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, size = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH':
        for p in o.data.polygons: p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_backface_culling = False; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.1, 0.1, 0.1); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_end = 100
for spec in a[3:]:
    n, c, o = spec.split(':'); c = Vector([float(x) for x in c.split(',')]); cd.ortho_scale = float(o)
    for vn, d in (('front', (0, -1, 0.05)), ('q34', (-1, -1.2, 0.4)), ('left', (1, 0, 0.05)), ('back', (0, 1, 0.05))):
        d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{pre}_{n}_{vn}.png'; bpy.ops.render.render(write_still=True)
