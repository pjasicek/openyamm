"""Mouth close-ups (Head bone centre) of a viewer GLB (rest pose, Standing frame 0): side, front, three-quarter, top.
Usage: blender -b -P mouth_views.py -- <glb> <label> <out dir>"""
import os, sys, math, bpy
from mathutils import Vector
glb, label, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:   # only the skinned creature mesh (the importer adds bone-shape icospheres)
    if o.type == 'MESH' and not any(m.type == 'ARMATURE' for m in o.modifiers): o.hide_render = True
act = bpy.data.actions.get('Standing') or bpy.data.actions.get('Fly')
if act: rig.animation_data.action = act
sc.frame_set(0)
pb = {b.name: b for b in rig.pose.bones}
print('BONES', [n for n in pb if 'eck' in n or 'ead' in n])
hb = next(b for n, b in pb.items() if n in ("Head", "B_Head", "mixamorig:Head")); head = rig.matrix_world @ ((hb.head + hb.tail) / 2)
neck = [rig.matrix_world @ b.head for n, b in pb.items() if 'neck' in n.lower()]
c = head
if os.environ.get('MOUTH_BONE'):                         # centre on a posed bone (Standing frame 0)
    _b = pb[os.environ['MOUTH_BONE']]; c = rig.matrix_world @ ((_b.head + _b.tail) / 2)
if os.environ.get('MOUTH_CENTER'):                       # explicit centre (rest-pose world metres, Blender axes)
    import json; c = Vector(json.loads(os.environ['MOUTH_CENTER']))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('MOUTH_SCALE', '.45'))
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.36, .36, .4, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 520
os.makedirs(out, exist_ok=True)
for view, d in {'side': (1, 0, .1), 'front': (0, -1, .1), 'q34': (.7, -.7, .3), 'top': (.1, -.2, 1), 'side_r': (-1, 0, .1)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
