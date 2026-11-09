"""Review frames of a clip from the exported textured GLB (Griffin: export/mm7_m258_lod0.glb):
EEVEE, a perspective 'party' camera in front of the monster at eye height (CAM env: front | side | tq), every STEP
frames. Writes <out_dir>/<clip>_<cam>_<frame>.png and frames.json. Args: -- <glb> <clip> <out_dir> [step] [cams]"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, clip, out = a[0], a[1], a[2]; step = float(a[3]) if len(a) > 3 else 2; cams = (a[4] if len(a) > 4 else 'front,side').split(',')
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == clip or x.name == clip)
arm.animation_data.action = act
if len(act.slots): arm.animation_data.action_slot = act.slots[0]
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 520, 520
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
# ground plane for contact reading
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, -0.5, 0))
gm = bpy.data.materials.new('g'); gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.35, 0.28, 0.22, 1)
bpy.context.object.data.materials.append(gm)
POS = {'front': (Vector((0.15, -6.5, 2.0)), Vector((0, -0.3, 1.3))), 'side': (Vector((7.0, -0.3, 1.6)), Vector((0, 0.0, 1.2))),
       'tq': (Vector((4.6, -5.0, 2.1)), Vector((0, -0.2, 1.3))), 'back': (Vector((-0.2, 6.5, 2.0)), Vector((0, 0.3, 1.3))),
       'face': (Vector((0.9, -2.8, 1.8)), Vector((0, -0.8, 1.45))), 'top': (Vector((0.01, -0.5, 7.5)), Vector((0, -0.2, 1.0)))}   # Griffin: 3.6 m span
FRAMES = os.environ.get('FRAMES')
cam_objs = {}
for c in cams:
    cam = bpy.data.objects.new('cam_' + c, bpy.data.cameras.new('cam_' + c)); sc.collection.objects.link(cam)
    p, t = POS[c]; cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 40; cam_objs[c] = cam
f0, f1 = act.frame_range; sc.render.fps = 30
rows = []
for c in cams:
    sc.camera = cam_objs[c]; row = []; f = f0
    seq = [float(x) for x in FRAMES.split(',')] if FRAMES else list(np.arange(f0, f1 + 1e-6, step))
    for f in seq:
        sc.frame_set(int(f), subframe=f - int(f))
        sc.render.filepath = os.path.join(out, f'{clip}_{c}_{f:05.1f}.png'); bpy.ops.render.render(write_still=True)
        row.append([sc.render.filepath, f'{clip} {c} f{f:g} {f / 24:.2f}s'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
print('RENDERED', clip, len(rows[0]), 'frames x', len(cams))
