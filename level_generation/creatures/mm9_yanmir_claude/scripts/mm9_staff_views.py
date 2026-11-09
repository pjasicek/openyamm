"""MM9's own staff (YANMIR.abc piece `staff`, its skin) rendered flat for the Codex brief and the comparison: head front, head side, a
piece of the shaft, the whole staff. Args: <true glb> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and not o.name.startswith('staff'): o.hide_render = True
    if o.name.startswith('Icosphere'): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = 900; sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.42, 0.42, 0.42)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, c, s, d in (('head', (-0.49, -0.5, 0.88), 0.45, (-0.3, -1, 0.15)), ('head_side', (-0.49, -0.5, 0.88), 0.45, (-1, 0.2, 0.15)),
                   ('shaft', (-0.47, -0.4, 0.2), 0.35, (-0.3, -1, 0.1)), ('full', (-0.45, -0.4, -0.2), 2.7, (-0.3, -1, 0.1))):
    cd.ortho_scale = s; v = Vector(d).normalized(); cam.location = Vector(c) + v * 5; cam.rotation_euler = (-v).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
print('DONE')
