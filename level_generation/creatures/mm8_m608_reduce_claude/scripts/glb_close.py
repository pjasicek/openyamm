"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): MM8 Juggernaut head, torso, back,
shoulders (also with both arms collapsed, to show holes the arms cover), hands, rollers, band, attack, death and rubble.
Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'head_front': ('Standing', 0, 'Head', .34, (0, -1, .1)), 'head_q34': ('Standing', 0, 'Head', .34, (.7, -.7, .2)),
         'torso': ('Standing', 0, 'Chest', .62, (0, -1, .05)), 'back': ('Standing', 0, 'Chest', .7, (0, 1, .1)),
         'shoulder_l': ('Standing', 0, 'UpperArm_L', .34, (.4, .9, .5)), 'shoulder_r': ('Standing', 0, 'UpperArm_R', .34, (-.4, .9, .5)),
         'noarms_front': ('Standing', 0, 'Chest', .62, (.2, -1, .3)), 'noarms_back': ('Standing', 0, 'Chest', .62, (.2, 1, .4)),
         'hand_l': ('Standing', 0, 'Hand_L', .34, (.6, -.8, .2)), 'hand_r': ('Standing', 0, 'Hand_R', .34, (-.6, -.8, .2)),
         'rollers': ('Standing', 0, 'Roller_1', .8, (.4, -1, .25)), 'band': ('Standing', 0, 'Waist', .5, (.3, -1, .1)),
         'attack': ('Attack', 12, 'Chest', .95, (.5, -1, .2)), 'hit': ('Hit', 9, 'Chest', .95, (-.5, -1, .2)),
         'death': ('Death', 12, 'Root', 1.1, (.5, -1, .5)), 'dead': ('Dead', 0, 'Root', 1.0, (.5, -.8, .7))}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    bodies = [o for o in bpy.data.objects if o.type == 'MESH' and 'UpperArm_L' in o.vertex_groups]
    for o in bodies:
        arms = o.vertex_groups.new(name='ArmsAll'); idx = {g.index for g in o.vertex_groups if g.name.startswith(('UpperArm', 'Forearm', 'Hand'))}
        arms.add([v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in idx) > .5], 1.0, 'REPLACE')
        m = o.modifiers.new('NoArms', 'MASK'); m.vertex_group = 'ArmsAll'; m.invert_vertex_group = True
    for spot, (act, frame, b, size, d) in SPOTS.items():
        for o in bodies:  # noarms: mask out both arms to see what they cover
            o.modifiers['NoArms'].show_render = o.modifiers['NoArms'].show_viewport = spot.startswith('noarms')
        rig.animation_data.action = bpy.data.actions[act]
        if bpy.data.actions[act].slots:
            rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
        sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
