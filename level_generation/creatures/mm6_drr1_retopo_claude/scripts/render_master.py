"""Textured renders of the installed revision-04 master (mm6_drr1_claude/export/mm6_wyrm.blend) at the user's
review spots -> review/v4/<view>.png"""
import math, os, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'mm6_drr1_claude', 'export', 'mm6_wyrm.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Wyrm_Rig']
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.33, 0.34, 0.37, 1)
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 800, 600
V = {'face': ((0.0, -0.66, 0.31), (0, -0.40, 0.29)), 'head_side': ((0.30, -0.50, 0.36), (0, -0.43, 0.33)),
     'spines': ((0.35, 0.05, 0.42), (0, 0.05, 0.25)), 'leg_br': ((-0.45, 0.05, 0.12), (0, -0.05, 0.10)),
     'chest': ((0.0, -0.62, 0.12), (0, -0.33, 0.16)), 'paws': ((0.0, -0.42, 0.07), (0, -0.25, 0.02)),
     'full': ((1.1, -1.25, 0.45), (0, -0.05, 0.18)), 'eye': ((0.12, -0.50, 0.345), (0.005, -0.471, 0.334)),
     'side_r': ((-0.75, -0.12, 0.14), (0, -0.12, 0.10)), 'side_l': ((0.75, -0.12, 0.14), (0, -0.12, 0.10)), 'chest_low': ((0.0, -0.55, 0.08), (0, -0.33, 0.15))}
for name, (loc, tgt) in V.items():
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', os.environ.get('REA_OUT', 'v4'), f'{name}.png'); bpy.ops.render.render(write_still=True)
