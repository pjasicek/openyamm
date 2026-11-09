"""MM9 head close-ups for the Codex head and body briefs (bind pose). Args: glb outpng head_z ortho [tile]"""
import bpy, sys, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, hz, ortho = argv[0], argv[1], float(argv[2]), float(argv[3])
tile = int(argv[4]) if len(argv) > 4 else 512
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.name.startswith('Icosphere'):
        o.hide_render = True
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = tile
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (.42, .42, .42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, hz))
views = {'front': Vector((0, -1, 0.05)), 'left': Vector((1, 0, 0.05)), 'q34': Vector((-1, -1.25, .3)), 'back': Vector((0, 1, .05))}
paths = []
for v, d in views.items():
    d = d.normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    p = f'{out}_{v}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); paths.append(p)
print('HEADS', out)
