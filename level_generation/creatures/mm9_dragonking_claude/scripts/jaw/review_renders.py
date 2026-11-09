"""Review renders of a runtime GLB (LOD0 only), Eevee: head close-ups at clip times with a head-tracking camera.
Framings: f41 (41.png: head from the front, slightly low, mouth near closed), f42 (42.png: from the creature's left,
snout to image right, slightly above and in front), q34, side, low (into the mouth from the front, below).
Args: -- <glb> <out prefix> <Clip@seconds|bind> <framings comma> [size] [clay]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, when, frs = a[0], a[1], a[2], a[3].split(',')
size = int(a[4]) if len(a) > 4 else 800
clay = len(a) > 5 and a[5] == 'clay'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
body = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
if when == 'bind':
    arm.animation_data_clear()
    for b in arm.pose.bones: b.matrix_basis.identity()
else:
    clip, t = when.split('@'); t = float(t)
    act = next(x for x in bpy.data.actions if x.name == clip or x.name.endswith('|' + clip) or x.name.startswith(clip))
    arm.animation_data_create(); arm.animation_data.action = act
    fps = sc.render.fps / sc.render.fps_base
    f = t * fps + act.frame_range[0]
    sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
bpy.context.view_layer.update()
M = arm.matrix_world
hp = M @ arm.pose.bones['Xheadpiv'].head; sn = M @ arm.pose.bones['Xjaw'].head; hd = M @ arm.pose.bones['Xhead'].head
# head frame from the skull: forward = Xheadpiv -> Xhead (snout direction), up = world z projected
fwd = (hd - hp); fwd.normalize()
upw = Vector((0, 0, 1)); left = upw.cross(fwd).normalized(); up = fwd.cross(left).normalized()
hc = hp * 0.3 + hd * 0.7
L = (hd - hp).length
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.35, 0.36, 0.38, 1); bg.inputs[1].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.0
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(40), 0, math.radians(-25))
cd = bpy.data.cameras.new('cam'); cd.lens = 85; cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = float(a[6]) * L if len(a) > 6 else 9 * L
V = {'f41': (fwd * 1.0 - up * 0.12 + left * 0.08, 0.0),
     'f42': (left * 1.0 + fwd * 0.45 + up * 0.25, 0.0),
     'q34': (fwd * 1.0 + left * 0.6 + up * 0.2, 0.0),
     'q34r': (fwd * 1.0 - left * 0.6 + up * 0.2, 0.0),
     'side': (-left * 1.0 + fwd * 0.1, 0.0),
     'low': (fwd * 1.0 - up * 0.55 + left * 0.25, 0.0)}
if clay:
    cm = bpy.data.materials.new('clay'); cm.use_nodes = True
    next(n for n in cm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
    for o in body:
        for s in o.material_slots: s.material = cm
for nm in frs:
    d, _ = V[nm]
    target = hc - up * 0.15 * L
    cam.location = target + d.normalized() * D
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{nm}.png'; bpy.ops.render.render(write_still=True)
print('REVIEW', out, when, [x.name for x in bpy.data.actions][:3])
