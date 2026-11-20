"""Face, mane, torso and claw renders of a werewolf viewer GLB, textured (EEVEE) and clay (workbench with cavity).
The facing is the Jaw bone ahead of the Head bone, the toes ahead of the feet, or the gaze socket ahead of the head
(Medusa). Optional REA_CLIP=<clip>:<frame>.
<out>/<label>_<shot>[_clay].png. Args: -- <glb> <label> <out dir>"""
import bpy, sys, os, math
from mathutils import Vector
glb, label, out = sys.argv[sys.argv.index('--') + 1:][:3]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
clip, frame = os.environ.get('REA_CLIP', 'Standing:0').split(':')
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(int(frame))
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0
names = {b.name.lower().split(':')[-1].replace('b_', '').replace('_', ''): b for b in rig.pose.bones}
bone = lambda *keys: next(rig.matrix_world @ names[k].head for k in keys if k in names)
head, chest, hand = bone('head'), bone('spine02', 'spine2'), bone('righthand', 'rhand')
gaze = bpy.data.objects.get('Socket_Gaze')  # an empty on the head, not a bone
fwd = (bone('jaw') - head) if 'jaw' in names else (gaze.matrix_world.translation - head) if gaze else \
    (bone('ltoe0') - bone('lfoot') + bone('rtoe0') - bone('rfoot'))
fwd.z = 0; fwd.normalize(); side = Vector((-fwd.y, fwd.x, 0))
sun.rotation_euler = (-fwd + side * .5 + Vector((0, 0, -1.2))).to_track_quat('-Z', 'Y').to_euler()
face = head + fwd * .08
shots = {'face_front': (face + fwd * .8 + Vector((0, 0, .05)), face),
         'face_q34': (face + fwd * .55 + side * .55 + Vector((0, 0, .08)), face),
         'face_side': (face + side * .8, face),
         'mane_back': (head - fwd * .9 + Vector((0, 0, .15)), head + Vector((0, 0, -.1))),
         'torso': (chest + fwd * 1.6 + side * .4, chest + Vector((0, 0, -.15))),
         'whole': (chest + fwd * 3.6 + side * 1.2 + Vector((0, 0, -.2)), chest + Vector((0, 0, -.75))),
         'whole_back': (chest - fwd * 3.6 - side * 1.2 + Vector((0, 0, -.2)), chest + Vector((0, 0, -.75))),
         'hand': (hand + fwd * .45 - side * .35 + Vector((0, 0, .15)), hand)}
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
for engine in ('EEVEE', 'WORKBENCH'):
    try:
        sc.render.engine = 'BLENDER_' + engine + ('_NEXT' if engine == 'EEVEE' else '')
    except TypeError:
        sc.render.engine = 'BLENDER_' + engine
    if engine == 'WORKBENCH':
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True
        sh.cavity_type = 'BOTH'
    for k, (p, t) in shots.items():
        cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
        suffix = '_clay' if engine == 'WORKBENCH' else ''
        sc.render.filepath = os.path.join(out, f'{label}_{k}{suffix}.png'); bpy.ops.render.render(write_still=True)
print('FACEVIEWS', label, 'fwd', tuple(round(c, 2) for c in fwd))
