"""Textured face/neck/hand close-ups of a viewer GLB at the Standing pose (model faces -Y): review/retex/<label>_*.png.
Usage: blender -b -P face_views.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
B = lambda n: rig.matrix_world @ rig.pose.bones[n].head
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
for name, rot, e in [('Key', (math.radians(55), 0, math.radians(-30)), 3.0), ('Fill', (math.radians(70), 0, math.radians(140)), 1.2)]:
    s = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); s.data.energy = e; s.rotation_euler = rot; sc.collection.objects.link(s)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 640
head = B('B_Head') + Vector((0, 0, .07)); neck = B('B_Neck')
spots = {'face': (head, .30, {'front': (0, -1, .05), 'q34': (.6, -.8, .1), 'side': (1, 0, .05), 'back': (0, 1, .1), 'q34l': (-.6, -.8, .1)}),
         'neck': (neck + Vector((0, 0, .02)), .26, {'front': (0, -1, .2), 'back': (0, 1, .3), 'side': (-1, 0, .1)}),
         'hands': ((B('B_L_Hand') + B('B_R_Hand')) / 2 + Vector((0, 0, -.05)), 1.0, {'front': (0, -1, .1), 'back': (0, 1, .1)})}
out = os.path.join(HERE, 'review', 'retex'); os.makedirs(out, exist_ok=True)
for spot, (c, size, views) in spots.items():
    for view, d in views.items():
        dv = Vector(d).normalized(); cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(out, f'{label}_{spot}_{view}.png'); bpy.ops.render.render(write_still=True)
