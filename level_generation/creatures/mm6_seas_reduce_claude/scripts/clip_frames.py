"""One clip of a sea serpent viewer/runtime GLB as frames from the front and from above (textured):
<out>_<view>_<frame>.png (frame_strip.py joins them). Args: -- <glb> <clip> <out prefix> <frame,frame,...>"""
import bpy, sys, os
from mathutils import Vector
glb, clip, out, fr = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc.render.resolution_x = sc.render.resolution_y = 360
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.55, 0.6, 0.66, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (0.6, 0.3, 0.4)
pb = rig.pose.bones; M = rig.matrix_world
rig.animation_data.action = None
for b in pb: b.matrix_basis.identity()
bpy.context.view_layer.update()
head, neck, root = M @ pb['Head'].head, M @ pb['Spine_14'].head, M @ pb['Root'].head
fwd = head - neck; fwd.z = 0; fwd.normalize(); mid = root + Vector((0, 0, .55))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
views = {'front': (mid + fwd * 2.6, mid), 'top': (root + Vector((0, 0, 3.2)) + fwd * .01, root)}
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
frames = [int(f) for f in fr.split(',')]
for v, (p, t) in views.items():
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    for f in frames:
        sc.frame_set(f); sc.render.filepath = f'{out}_{v}_{f:02d}.png'; bpy.ops.render.render(write_still=True)
print('CLIPFRAMES', out)
