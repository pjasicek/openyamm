"""MM9 clip strips: render clips at N evenly spaced frames from one source GLB. Args: glb outdir name size [clips comma]"""
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, size = argv[0], argv[1], int(argv[2])
sel = argv[3].split(',') if len(argv) > 3 and argv[3] else None
nfr = int(argv[4]) if len(argv) > 4 else 8
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.type == 'MESH' and os.environ.get('ONLYS') and 'Sphere05b' not in o.name: o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE' if os.environ.get('CLAY') else 'TEXTURE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 2.6; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((-0.06, 0, 0.8))
d = Vector((-1, -1.25, 0.35)).normalized(); cam.location = c + d * 10
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
print('ACTIONS', [(a.name, a.frame_range[:]) for a in bpy.data.actions])
for a in bpy.data.actions:
    nm = a.name
    if sel and nm not in sel: continue
    if a.name.startswith('Icosphere') or a.name=='static_model' or a.name.startswith('Armature'): continue
    arm.animation_data.action = a
    try: arm.animation_data.action_slot = a.slots[0]
    except Exception: pass
    f0, f1 = a.frame_range
    for k in range(nfr):
        f = f0 + (f1 - f0) * k / (nfr - 1)
        sc.frame_set(int(f))
        sc.render.filepath = os.path.join(out, f'{nm}_{k:02d}.png')
        bpy.ops.render.render(write_still=True)
print('POSES done')
