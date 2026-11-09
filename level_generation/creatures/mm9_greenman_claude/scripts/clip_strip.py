"""Workbench strip of clips on a GLB: for each 'action@f1,f2,..' render front and side views of the textured mesh.
Args: <glb> <out png> <size> <ortho> <cz> action@frames ..."""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, size, ortho, cz = argv[0], argv[1], int(argv[2]), float(argv[3]), float(argv[4])
specs = argv[5:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and ('_LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Icosphere')):
        o.hide_render = True
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
tmp = os.path.dirname(out) + '/_strip_tmp'; os.makedirs(tmp, exist_ok=True)
files = []
for spec in specs:
    name, frames = spec.split('@')
    act = bpy.data.actions[name]; arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    for f in frames.split(','):
        sc.frame_set(int(f))
        for v, d in [x for x in (('front', Vector((0, -1, 0.05))), ('side', Vector((1, 0, 0.05))), ('back', Vector((0, 1, 0.05))), ('top', Vector((0.0, -0.3, 1)))) if x[0] in os.environ.get('SVIEWS', 'front,side').split(',')]:
            c = Vector((float(os.environ.get('CX', 0)), float(os.environ.get('CY', 0)), cz)); cam.location = c + d.normalized() * 10
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            p = f'{tmp}/{name}_{f}_{v}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); files.append((f'{name} {f} {v}', p))
import json; json.dump(files, open(tmp + '/list.json', 'w'))
print('STRIP', len(files))
