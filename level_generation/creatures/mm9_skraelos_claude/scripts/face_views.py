"""EEVEE renders of a textured GLB in a viewer-like light (key from front-above-left, soft fill, sky ambient, no
shadows on the face from the hair): head close-ups (front, 3/4, true profile, low 3/4 from below, party view from
above at 2.1 m) and full body (front, 3/4, back), plus a 128 px face simulation. The figure faces -Y (Blender).
Args: <glb> <out dir> <prefix> <head centre z (Blender, floor 0)> <head ortho> [<full ortho>]
Env: POSE=<action>@<frame> poses the armature; VARIANT=<material name substring> swaps the body/head base colour
images to those of the materials whose names contain it (KHR variants are not applied by the importer);
HEADIMG=<png> replaces the head material's base colour image; VIEWS=comma list to limit."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, hz, hortho = a[0], a[1], a[2], float(a[3]), float(a[4])
fortho = float(a[5]) if len(a) > 5 else None
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and ('_LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if arm and arm.animation_data:
    arm.animation_data.action = None
for pb in (arm.pose.bones if arm else []):
    pb.matrix_basis.identity()
if os.environ.get('POSE') and arm:
    name, fr = os.environ['POSE'].split('@')
    act = bpy.data.actions[name]
    if not arm.animation_data:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(float(fr)))
if os.environ.get('HEADIMG'):
    img = bpy.data.images.load(os.environ['HEADIMG'])
    for m in bpy.data.materials:
        if m.use_nodes and 'Head' in m.name:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image and 'basecolor' in n.image.name.lower() or (n.type == 'TEX_IMAGE' and n.outputs[0].links and n.outputs[0].links[0].to_socket.name == 'Base Color'):
                    n.image = img
bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.57, 0.62, 1); bg.inputs[1].default_value = 0.55
sc.view_settings.view_transform = 'Standard'
def sun(name, rot, e, col=(1, 0.97, 0.92)):
    l = bpy.data.lights.new(name, 'SUN'); l.energy = e; l.color = col
    try:
        l.use_shadow = False
    except Exception:
        pass
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.rotation_euler = rot
sun('key', (math.radians(50), 0, math.radians(-25)), 2.6)
sun('fill', (math.radians(70), 0, math.radians(140)), 0.8, (0.9, 0.93, 1.0))
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
H = Vector([float(x) for x in os.environ['HC'].split(',')]) if os.environ.get('HC') else Vector((0, 0, hz))
views = {'front': (Vector((0, -1, 0)), hortho, H, 700), 'q34': (Vector((-0.8, -1, 0.05)), hortho, H, 700),
         'profile': (Vector((1, 0, 0)), hortho, H, 700), 'low': (Vector((-0.6, -1, -0.65)), hortho, H, 700),
         'party': (Vector((0, -2.1, 1.1)), hortho * 1.6, H, 700), 'ear_l': (Vector((1, 0.15, 0)), hortho * 0.7, H, 600),
         'ear_r': (Vector((-1, 0.15, 0)), hortho * 0.7, H, 600)}
if fortho:
    C = Vector((0, 0, hz * 0.5))
    views.update({'body_front': (Vector((0, -1, 0.1)), fortho, C, 800), 'body_q34': (Vector((-0.9, -1, 0.15)), fortho, C, 800),
                  'body_back': (Vector((0, 1, 0.1)), fortho, C, 800)})
sel = os.environ.get('VIEWS')
for k, (d, o, c, size) in views.items():
    if sel and k not in sel.split(','):
        continue
    d = d.normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = o
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{k}.png')
    bpy.ops.render.render(write_still=True)
print('FACEVIEWS', prefix)
