"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). MM7 Devil spots: face, mouth, horns, shoulder spikes, chest, both
clawed hands, the claws in the attack, feet, heel spurs, tail, the corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
# Monk spots (glTF +Z faces the camera at (0, -1) after import: Blender -Y front)
SPOTS = {'face_front': ('Standing', 0, 'Bip01 Head', .32, (0, -1, .1)), 'face_q34': ('Standing', 0, 'Bip01 Head', .36, (-.7, -.7, .2)),
         'hood_back': ('Standing', 0, 'Bip01 Head', .55, (.3, 1, .5)), 'chest': ('Standing', 0, 'Bip01 Spine3', .8, (0, -1, .1)),
         'chest_q34': ('Standing', 0, 'Bip01 Spine3', .8, (-.7, -.7, .2)), 'back': ('Standing', 0, 'Bip01 Spine3', .9, (0, 1, .15)),
         'sleeve_r': ('Standing', 0, 'Bip01 R Forearm', .5, (-.8, -.5, .3)), 'hands': ('Standing', 0, 'Bip01 Spine', .7, (0, -1, .3)), 'hand_l': ('Standing', 0, 'V:Bip01 L Hand', .3, (.5, -.8, .3)), 'hand_r': ('Standing', 0, 'V:Bip01 R Hand', .3, (-.6, -.7, .3)), 'fist': ('AttackMelee', 12, 'V:Bip01 R Hand', .35, (-.6, -.7, .3)), 'pray_hands': ('Pray', 30, 'V:Bip01 L Hand', .4, (0, -1, .2)),
         'robe': ('Standing', 0, 'Bip01 Spine', 1.4, (.2, -1, -.1)), 'robe_side': ('Standing', 0, 'Bip01 Spine', 1.4, (-1, -.2, -.05)),
         'hem': ('Standing', 0, 'Bip01 R Foot', .9, (-.3, -1, .1)),
         'cast': ('AttackRanged3', 20, 'Bip01 Spine3', 1.6, (-.6, -.8, .2)), 'run': ('Running', 6, 'Bip01 Spine', 2.0, (-1, -.2, .2)),
         'walk': ('Walking', 10, 'Bip01 Spine', 2.0, (-.6, -.8, .1)), 'pray': ('Pray', 30, 'Bip01 Spine', 2.0, (-.6, -.8, .3)), 'pray_robe': ('Pray', 9, 'Bip01 Spine', 1.4, (.2, -1, .3)), 'pray_robe_back': ('Pray', 9, 'Bip01 Spine', 1.4, (-.2, 1, .3)), 'death_arm': ('Death', 40, 'Bip01 R UpperArm', .7, (-.3, -.3, 1)),
         'death': ('Death', 36, 'Bip01 Spine', 2.2, (.6, -.6, .6)), 'death2': ('Death2', 15, 'Bip01 Spine', 2.2, (-.6, -.6, .6))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == os.environ.get('REA_NODE', 'Monk'))
    vg = {g.index: g.name for g in body.vertex_groups}
    dom = [vg[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in body.data.vertices]
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = bpy.data.actions[act]
        if bpy.data.actions[act].slots:
            rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
        sc.frame_set(frame)
        if b.startswith('V:'):
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
            ids = [i for i, n in enumerate(dom) if n == b[2:]]
            c = sum((body.matrix_world @ m.vertices[i].co for i in ids), Vector()) / len(ids); ev.to_mesh_clear()
        else:
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            if mode == 'clay' and os.environ.get('NO_CLAY'):
                continue
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
