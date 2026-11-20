"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). Skeleton spots: the face sheet (front, 3/4, profile, low 3/4, party), chest,
back, boots, both fists, attack, corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {  # skeleton (1.79 m, faces -y; Blender frames at 30 fps here): the face sheet of the brief plus the cut pieces
    'face_front': ('Standing', 0, 'Bip01 Head', .34, (0, -1, .05)), 'face_q34': ('Standing', 0, 'Bip01 Head', .38, (-.7, -.7, .15)),
    'face_profile': ('Standing', 0, 'Bip01 Head', .4, (-1, 0, .02)), 'face_low34': ('Standing', 0, 'Bip01 Head', .4, (.6, -.7, -.5)),
    'party': ('Standing', 0, 'Bip01 Neck', .9, (0, -1, .15)), 'head_back': ('Standing', 0, 'Bip01 Head', .42, (.3, 1, .4)),
    'chest': ('Standing', 0, 'Bip01 Spine2', .6, (0, -1, .1)), 'chest_q34': ('Standing', 0, 'Bip01 Spine2', .6, (.7, -.7, .2)),
    'back': ('Standing', 0, 'Bip01 Spine2', .65, (0, 1, .15)), 'pelvis': ('Standing', 0, 'Bip01 Pelvis', .5, (-.3, -1, .2)),
    'legs': ('Standing', 0, 'Bip01 R Calf', .8, (-.4, -1, .2)), 'feet': ('Standing', 0, 'Bip01 R Foot', .3, (-.5, -.8, .5)),
    'fist_r': ('Standing', 0, 'Bip01 R Hand', .3, (-.6, -.7, .3)), 'fist_l': ('Standing', 0, 'Bip01 L Hand', .3, (.5, -.8, .3)),
    'arm_r': ('Standing', 0, 'Bip01 R Forearm', .6, (-.4, -1, .2)),
    'attack': ('AttackMelee', 12, 'Bip01 Spine1', 1.7, (-.6, -.8, .2)), 'death': ('Death', 33, 'Bip01 Spine', 1.9, (.6, -.6, .6)),
    'whole': ('Standing', 0, 'Bip01 Spine', 2.0, (.6, -.8, .2)),
    'hand_r_close': ('Standing', 0, 'Bip01 R Hand', .16, (-.3, -1, .2)), 'hand_l_close': ('Standing', 0, 'Bip01 L Hand', .16, (.5, -1, .3)),
    'hand_l_back': ('Standing', 0, 'Bip01 L Hand', .16, (.8, .4, .6)),
    # skelwar arm-gate frames (48 fps frame f -> 30 fps f * 0.625)
    'am2_l_a': ('AttackMelee2', 2, 'Bip01 L Hand', .4, (.7, -.7, .3)), 'am2_l_b': ('AttackMelee2', 3, 'Bip01 L Hand', .4, (-.2, -1, .1)),
    'am2_l_c': ('AttackMelee2', 3, 'Bip01 L Hand', .4, (1, .2, .1)),
    # skirt-gate frames: Walking 48 fps frame 48 (= 30), Backpedal frame 4 (= 2), from behind and the left
    'walk_back': ('Walking', 30, 'Bip01 Pelvis', .9, (.2, 1, .1)), 'walk_left': ('Walking', 30, 'Bip01 Pelvis', .9, (1, .3, .1)),
    'hit_l_a': ('Hit', 20, 'Bip01 L Forearm', .6, (.7, -.7, .2)), 'hit_l_b': ('Hit', 20, 'Bip01 L Forearm', .6, (1, .3, -.1)),
    'hit_l_c': ('Hit', 4, 'Bip01 L Hand', .5, (.7, -.7, .2)),
    # piece contacts whose rest gap grew (head_contacts.py PRIM=0): knee/boot top, shoulder/humerus top, wrist
    'knee_r': ('Standing', 0, 'Bip01 R Calf', .3, (-.5, -.8, .3)), 'knee_r_back': ('Walking', 10, 'Bip01 R Calf', .3, (-.3, 1, .2)),
    'shoulder_r': ('Standing', 0, 'Bip01 R UpperArm', .35, (-.6, -.6, -.4)), 'shoulder_r_back': ('Standing', 0, 'Bip01 R UpperArm', .35, (-.4, 1, .1)),
    'wrist_l': ('Standing', 0, 'Bip01 L Forearm', .35, (.6, -.7, -.3)),
    # detached-audit frames of the skirt plates (24 fps frame f -> 30 fps f * 1.25)
    'walk_plate_fr': ('Walking', 6, 'Bip01 Pelvis', .8, (-.7, -.7, .1)), 'walk_plate_fr2': ('Walking', 6, 'Bip01 Pelvis', .8, (-1, .1, .1)),
    'bp_back': ('Backpedal', 2, 'Bip01 Pelvis', .9, (.2, 1, .1)), 'bp_left': ('Backpedal', 2, 'Bip01 Pelvis', .9, (1, .3, .1))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == os.environ.get('REA_NODE', 'Skel'))
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
