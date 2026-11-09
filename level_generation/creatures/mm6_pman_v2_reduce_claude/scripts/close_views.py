"""Close renders of viewer GLBs (Standing frame 0): head and right hand, front and three-quarter.
Usage: blender -b -P close_views.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and 'Ash' in o.name: o.hide_render = True
act = bpy.data.actions.get('Standing') or bpy.data.actions.get('Flight')
if act: rig.animation_data.action = act
sc.frame_set(0)
pb = {b.name: b for b in rig.pose.bones}
ALIASES = {':Head': ('head',), ':RightHand': ('righthand', 'r_hand', 'hand.r', 'hand_r'),
           ':RightFoot': ('rightfoot', 'r_foot', 'foot.r', 'foot_r')}
pick = lambda key: next(rig.matrix_world @ b.head for n, b in pb.items()
                        if any(n.lower().replace('mixamorig:', '').endswith(a) for a in ALIASES[key]))
spots = {'head': (pick(':Head'), .45), 'hand': (pick(':RightHand'), .4), 'whole': ((pick(':Head') + pick(':RightFoot')) / 2, 2.0)}
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 600
sc.render.engine = 'BLENDER_EEVEE'
for spot, (c, size) in spots.items():
    for view, d in {'front': (0, -1, .1), 'q34': (.7, -.7, .2), 'side': (1, 0, .1)}.items():
        # the demon faces +X in the GLB (actors.yml yaw_offset -90 deg): rotate the view directions
        dv = Vector((-d[1], d[0], d[2])).normalized()
        cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(HERE, 'review/close', f'{label}_{spot}_{view}.png'); bpy.ops.render.render(write_still=True)
