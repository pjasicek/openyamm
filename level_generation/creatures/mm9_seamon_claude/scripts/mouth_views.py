"""Close-up renders of the Sea Monster's head/mouth from a GLB at clip times (the user's review framings).

Args: <glb> <outdir> <prefix> <shot,shot,...> [size]
Shot = <name>:<clip>@<seconds>:<view>, clip '-' = bind pose. Views (in the head bone's frame, so they follow the head):
  front  - from the front, slightly above (user 33/34)
  side   - from the creature's right, slightly in front and above (user 35)
  low    - from the front and below, looking into the open mouth (user 32)
  sidel  - from the creature's left
  close  - texture close-up of the cheek/eye from the front three-quarter
Workbench, studio light, textured, backface culling ON (the materials are single-sided in game).
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, shots = argv[0], argv[1], argv[2], argv[3].split(',')
size = int(argv[4]) if len(argv) > 4 else 900
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arms = [o for o in sc.objects if o.type == 'ARMATURE']
arm = arms[0] if arms else None
for o in sc.objects:
    if o.type == 'MESH' and (o.name.startswith('Icosphere') or 'LOD' in o.name and 'LOD0' not in o.name):
        o.hide_render = True
HEAD_PT = Vector((0.0, -1.62, 0.42))
bind = arm.matrix_world @ arm.data.bones['Bone07'].matrix_local if arm else Matrix.Identity(4)
local_pt = bind.inverted() @ HEAD_PT
VIEWS = {'inside': (Vector((0.0, -1, -0.05)), 0.9, 35), 'insidel': (Vector((0.6, -1, 0.0)), 0.9, 35),
         'front': (Vector((0, -1, 0.32)), 1.45, 35), 'side': (Vector((-1, -0.35, 0.22)), 1.4, 35),
         'low': (Vector((0, -1, -0.25)), 1.35, 35), 'sidel': (Vector((1, -0.35, 0.22)), 1.4, 35),
         'close': (Vector((-0.55, -1, 0.35)), 0.85, 35)}
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError as e:
    print(e)
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE'
sh.show_backface_culling = True
sc.render.resolution_x = size
sc.render.resolution_y = size
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new('w') if sc.world is None else sc.world
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('cam')
cd.lens = 35
cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd)
sc.collection.objects.link(cam)
sc.camera = cam
fps = sc.render.fps / sc.render.fps_base
for shot in shots:
    name, pose, view = shot.split(':')
    clip, t = pose.split('@')
    if arm is None:
        pass
    elif clip == '-':
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[clip]
        arm.animation_data_create()
        arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        f = float(t) * fps
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    bpy.context.view_layer.update()
    hm = arm.matrix_world @ arm.pose.bones['Bone07'].matrix if arm else Matrix.Identity(4)
    target = hm @ local_pt
    d, dist, lens = VIEWS[view]
    d = (hm.to_3x3().normalized() @ (bind.to_3x3().normalized().inverted() @ d)).normalized()
    cd.lens = lens
    cam.location = target + d * dist
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{name}.png')
    bpy.ops.render.render(write_still=True)
print('MOUTH VIEWS', prefix, len(shots))
