"""Clay render of each LOD mesh of the runtime GLB, front. Args: <glb> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .7, .62)
sc.render.resolution_x = 500; sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.4; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 1)); cam.location = c + Vector((-.7, -1, .1)).normalized() * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
ms = [o for o in bpy.data.objects if o.type == 'MESH' and 'Shadow' not in o.name and not o.name.startswith('Ico')]
print('MESHES', [(o.name, len(o.data.polygons)) for o in ms])
for k in ('LOD1', 'LOD2', 'LOD3'):
    for o in ms: o.hide_render = k not in o.name
    sc.render.filepath = f'{a[1]}_{k}.png'; bpy.ops.render.render(write_still=True)
for o in ms: o.hide_render = ('LOD' in o.name)
sc.render.filepath = f'{a[1]}_LOD0.png'; bpy.ops.render.render(write_still=True)
