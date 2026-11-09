"""Feet close-ups from the exported textured GLB (user review 2026-10-20: rolled soles): EEVEE, low cameras at foot
height in front and from the side, for listed clip:frame items. Writes review/feet/<clip>_<frame>_<cam>.png.
Args: -- <glb> clip:frame [...]"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, items = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'feet'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 640, 400
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
gm = bpy.data.materials.new('g'); gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.35, 0.28, 0.22, 1)
bpy.context.object.data.materials.append(gm)
CAMS = {'front': (Vector((0.0, -1.6, 0.18)), Vector((0, -0.1, 0.1))), 'side': (Vector((1.6, -0.1, 0.18)), Vector((0, -0.1, 0.1)))}
cams = {}
for c, (p, t) in CAMS.items():
    cam = bpy.data.objects.new(c, bpy.data.cameras.new(c)); sc.collection.objects.link(cam)
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 35; cams[c] = cam
for it in items:
    clip, fr = it.split(':'); fr = float(fr)
    act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == clip or x.name == clip)
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(fr), subframe=fr - int(fr))
    for c, cam in cams.items():
        sc.camera = cam; sc.render.filepath = os.path.join(out, f'{clip}_{int(fr):03d}_{c}.png')
        bpy.ops.render.render(write_still=True)
print('FEET', len(items), 'items x', len(cams))
