"""Textured whole-body and head frames of a viewer GLB over several clips: review/retex/<label>_pose_<clip>_<f>.png.
Usage: blender -b -P pose_views.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; sc.render.fps = 30; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
s = bpy.data.objects.new('Key', bpy.data.lights.new('Key', 'SUN')); s.data.energy = 3; s.rotation_euler = (math.radians(55), 0, math.radians(-30)); sc.collection.objects.link(s)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 420
for clip, frac in [('Walking', .5), ('Hit', .5), ('Death', .5), ('Death', 1.0), ('Fidget', .5)]:
    a = bpy.data.actions[clip]; rig.animation_data.action = a; f = int(a.frame_range[0] + frac * (a.frame_range[1] - a.frame_range[0])); sc.frame_set(f)
    head = rig.matrix_world @ rig.pose.bones['B_Head'].head
    for spot, c, size in [('whole', Vector((head.x, head.y, max(head.z * .5, .4))), 2.0), ('head', head + Vector((0, 0, .06)), .4)]:
        dv = Vector((.5, -.85, .25)).normalized(); cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(HERE, 'review', 'retex', f'{label}_pose_{clip}_{int(frac * 100)}_{spot}.png'); bpy.ops.render.render(write_still=True)
