"""Sea serpent renders of a viewer GLB, textured (EEVEE) and clay (workbench with cavity): whole body from four sides
and the head from the front, side and above (forward = Spine_14 -> Head, horizontal). Optional REA_CLIP=<clip>:<frame>.
<out>/<label>_<shot>[_clay].png. Args: -- <glb> <label> <out dir>"""
import bpy, sys, os
from mathutils import Vector
glb, label, out = sys.argv[sys.argv.index('--') + 1:][:3]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Foam')): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
clip, frame = os.environ.get('REA_CLIP', 'Standing:0').split(':')
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(int(frame))
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.55, 0.6, 0.66, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.0
pb = rig.pose.bones; M = rig.matrix_world
head = M @ pb['Head'].head; neck = M @ pb['Spine_14'].head; root = M @ pb['Root'].head
fwd = head - neck; fwd.z = 0; fwd.normalize(); side = Vector((-fwd.y, fwd.x, 0))
sun.rotation_euler = (-fwd + side * .5 + Vector((0, 0, -1.2))).to_track_quat('-Z', 'Y').to_euler()
mid = (head + root) / 2; hc = head + fwd * .05
shots = {'whole_front': (mid + fwd * 2.4, mid), 'whole_side': (mid + side * 2.4, mid), 'whole_back': (mid - fwd * 2.4, mid),
         'whole_q34': (mid + (fwd + side).normalized() * 2.4 + Vector((0, 0, .5)), mid),
         'head_front': (hc + fwd * .6 + Vector((0, 0, .1)), hc), 'head_side': (hc + side * .6, hc),
         'head_q34': (hc + (fwd - side).normalized() * .55 + Vector((0, 0, .2)), hc),
         'head_below': (hc + fwd * .35 + Vector((0, 0, -.35)), hc),
         'spine_side': (mid + side * .9 - fwd * .2, mid - fwd * .1), 'spine_back': (mid - fwd * .9 + side * .3, mid)}
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
for engine in ('EEVEE', 'WORKBENCH'):
    try: sc.render.engine = 'BLENDER_' + engine + ('_NEXT' if engine == 'EEVEE' else '')
    except TypeError: sc.render.engine = 'BLENDER_' + engine
    if engine == 'WORKBENCH':
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
    for k, (p, t) in shots.items():
        cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{k}{"_clay" if engine == "WORKBENCH" else ""}.png'); bpy.ops.render.render(write_still=True)
print('SEASVIEWS', label)
