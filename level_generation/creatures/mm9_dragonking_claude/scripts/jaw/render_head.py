"""Head close-ups of a blend or GLB at a clip time. Eevee, textured (and optional clay / part colours).
Args: -- <blend|glb> <out_prefix> <action|-> <seconds> [views comma list] [size] [look textured|clay|both]
Views: side (creature's left, snout to image right, like 42.png), q34 (front three-quarter from the left, high),
front, below, q34r (from the right), inside (camera inside the mouth looking back), top."""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, act, t = a[0], a[1], a[2], float(a[3])
views = a[4].split(',') if len(a) > 4 else ['side', 'q34', 'front']
size = int(a[5]) if len(a) > 5 else 700
looks = {'both': ['textured', 'clay']}.get(a[6] if len(a) > 6 else 'textured', [a[6] if len(a) > 6 else 'textured'])
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.parent != rig and o.find_armature() != rig or 'LOD' in o.name or 'Shadow' in o.name
                             or o.name.startswith('MM9') or o.name.endswith('.mesh') or o.name == 'MeshyPosed'):
        o.hide_render = True
body = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
if act != '-':
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions[act]
    sc.render.fps = 30; sc.render.fps_base = 1
    f = t * 30
    sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
else:
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
M = rig.matrix_world
hp = M @ rig.pose.bones['Xheadpiv'].head
sn = M @ rig.pose.bones['Xjaw'].head
fwd = (sn - hp); fwd.z = 0; fwd.normalize()
left = Vector((0, 0, 1)).cross(fwd).normalized()   # creature's left? (fwd -Y -> left = +x... checked by eye)
hc = hp * 0.45 + sn * 0.55
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs[0].default_value = (0.35, 0.37, 0.4, 1); bg.inputs[1].default_value = 0.9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.0
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), 0, math.radians(-20))
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 85; cd.clip_start = 0.01
D = 18.0
up = Vector((0, 0, 1))
V = {'side': (hc + (left * 1.0 + fwd * 0.25 + up * 0.05).normalized() * D, hc),
     'q34': (hc + (left * 0.55 + fwd * 1.0 + up * 0.25).normalized() * D, hc),
     'q34r': (hc + (-left * 0.55 + fwd * 1.0 + up * 0.25).normalized() * D, hc),
     'front': (hc + (fwd * 1.0 + up * 0.08).normalized() * D, hc),
     'below': (hc + (fwd * 0.6 - up * 1.0 + left * 0.2).normalized() * D, hc),
     'top': (hc + (fwd * 0.3 + up * 1.0).normalized() * D, hc),
     'q34hi': (hc + (left * 0.7 + fwd * 1.0 + up * 0.6).normalized() * D, hc)}
clay = bpy.data.materials.new('clay'); clay.use_nodes = True
cb = next(n for n in clay.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
cb.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1); cb.inputs['Roughness'].default_value = 0.6
orig = {o.name: [s.material for s in o.material_slots] for o in body}
for look in looks:
    for o in body:
        for i, s in enumerate(o.material_slots):
            s.material = orig[o.name][i] if look == 'textured' else clay
    for name in views:
        loc, tgt = V[name]
        cam.location = loc
        cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{name}_{look}.png'
        bpy.ops.render.render(write_still=True)
print('RENDERED', out, views, looks, 'fwd', tuple(round(x, 3) for x in fwd), 'left', tuple(round(x, 3) for x in left))
