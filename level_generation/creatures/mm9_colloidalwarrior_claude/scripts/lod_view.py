"""LOD0-3 side by side (clay, rest pose, Standing frame 0). Args: <glb> <out png prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('MESHES', [(o.name, len(o.data.polygons)) for o in meshes])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .73, .7)
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.4; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
d = Vector((-1, -1.2, 0.35)).normalized(); c = Vector((0, 0, 1.0)); cam.location = c + d * 8; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
for k in range(4):
    want = [o for o in meshes if (('LOD%d' % k) in o.name if k else ('LOD' not in o.name)) and 'Shadow' not in o.name]
    for o in meshes: o.hide_render = o not in want
    sc.render.filepath = f'{a[1]}_lod{k}.png'; bpy.ops.render.render(write_still=True)
