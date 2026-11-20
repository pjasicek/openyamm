"""Close renders of the left hand (REA_HAND=L, default) or right hand of a viewer GLB in Standing frame 0, six views,
textured or clay (REA_CLAY). -> review/hands/<label>_<view>.png. Usage: blender -b -P hand_views.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions[os.environ.get('REA_CLIP', 'Standing')]; sc.frame_set(int(os.environ.get('REA_FRAME', '0')))
side = os.environ.get('REA_HAND', 'L')
hb = rig.pose.bones[f'B_{side}_Hand']; c = rig.matrix_world @ (hb.head + (hb.tail - hb.head) * 1.6)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .2
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 450
sc.render.engine = 'BLENDER_EEVEE'
if os.environ.get('REA_CLAY'):
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.show_cavity = True; sc.display.shading.single_color = (.7, .66, .6)
os.makedirs(os.path.join(HERE, 'review/hands'), exist_ok=True)
for view, d in {'front': (0, -1, .1), 'back': (0, 1, .1), 'out': (1 if side == 'L' else -1, 0, .1),
                'in': (-1 if side == 'L' else 1, -.15, .1), 'below': (.2, -.3, -1), 'q34': (.7 if side == 'L' else -.7, -.7, .2)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review/hands', f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
