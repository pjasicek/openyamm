"""Close-ups of the school straight from GLBs (the file's own normals; no weld): Fish00 (the largest) from the
side, top, front and three-quarter rear, a small fish (Fish03, scale 0.31) and the whole school, textured (EEVEE) and
clay (workbench). Usage: blender -b -P fish_views.py -- <label=glb,...> [clip frame] -> review/close/<label>_<view>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]
clip, frame = (args[1], float(args[2])) if len(args) > 2 else ('Swim', 0.0)
VIEWS = {'side': ('Fish00_Body', .85, (1, 0, .05)), 'top': ('Fish00_Body', .85, (0.05, 0, 1)),
         'front': ('Fish00_Body', .45, (0, -1, .1)), 'rear': ('Fish00_Body', .6, (.5, 1, .35)),
         'fins': ('Fish00_Body', .42, (-1, -.35, -.25)), 'dorsal': ('Fish00_Body', .25, (-1, .15, .35)), 'small': ('Fish03_Body', .3, (1, -.3, .2)), 'school': (None, 2.6, (1, -.6, .25))}
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb) if not os.path.isabs(glb) else glb)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == clip or a.name == clip)
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    fr = act.frame_range[0] + frame * 24; sc.frame_set(int(fr), subframe=fr - int(fr))
    mesh = bpy.data.objects['School']
    for view, (b, size, d) in VIEWS.items():
        if b:
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        else:
            bb = [mesh.matrix_world @ Vector(v) for v in mesh.bound_box]; c = sum(bb, Vector()) / 8
        cam.location = c + Vector(d).normalized() * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size; cam.data.clip_end = 20
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{view}_{mode}.png')
            bpy.ops.render.render(write_still=True)
