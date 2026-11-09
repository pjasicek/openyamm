"""Clay frames of clips from a glb. Args: <glb> <outdir> clip:time[:view] ... ; env ORTHO, CENTER"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUTD, SP = a[0], a[1], a[2:]
os.makedirs(OUTD, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene; sc.render.fps = 30
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_cavity = True; sh.show_backface_culling = False
S = int(os.environ.get('SIZE', 520)); sc.render.resolution_x = sc.render.resolution_y = S
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.2, 0.2, 0.22); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get('ORTHO', 3.6)); cd.clip_end = 100; cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'q34': (-1, -1.25, 0.3), 'q34l': (1, -1.25, 0.3), 'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'back': (0, 1, 0.05), 'right': (-1, 0, 0.05)}
c0 = Vector([float(x) for x in os.environ.get('CENTER', '0,0,1.2').split(',')])
fs = []
for sp in SP:
    q = sp.split(':'); clip, t = q[0], float(q[1]); v = q[2] if len(q) > 2 else 'q34'
    act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(clip))
    if not arm.animation_data: arm.animation_data_create()
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.render.fps = 24
    sc.frame_set(0, subframe=0); sc.frame_float = t * 24; bpy.context.view_layer.update()
    d = Vector(D[v]).normalized(); cam.location = c0 + d * 10
    cam.rotation_euler = (c0 - cam.location).to_track_quat('-Z', 'Y').to_euler()
    f = os.path.join(OUTD, f'{clip}_{t:.2f}_{v}.png'); sc.render.filepath = f; bpy.ops.render.render(write_still=True); fs.append(f)
print('FRAMES', len(fs))
