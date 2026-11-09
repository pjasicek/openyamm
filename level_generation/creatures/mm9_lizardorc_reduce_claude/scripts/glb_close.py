"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). Lizard-Orc spots: the face sheet (front, 3/4, profile, low 3/4), full body front/3-4/back,
chest, back, pauldrons, both hands (the fist in the attack, the cast hand), hips, legs, feet, tail, cutlass, motion frames. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
# Lizard-Orc (glTF import: the figure faces -y). Face sheet: front close-up, 3/4, true profile, low 3/4; body and motion spots
SPOTS = {'face_front': ('Standing', 0, 'Bip01 Head', .42, (0, -1, .05)), 'face_q34': ('Standing', 0, 'Bip01 Head', .46, (-.7, -.7, .15)),
         'face_profile': ('Standing', 0, 'Bip01 Head', .46, (-1, 0, .02)), 'face_low34': ('Standing', 0, 'Bip01 Head', .46, (.6, -.7, -.45)),
         'full_front': ('Standing', 0, 'Bip01 Spine1', 2.0, (0, -1, .08)), 'full_q34': ('Standing', 0, 'Bip01 Spine1', 2.0, (-.7, -.7, .15)),
         'full_back': ('Standing', 0, 'Bip01 Spine1', 2.0, (.1, 1, .12)),
         'chest': ('Standing', 0, 'Bip01 Spine2', .7, (0, -1, .1)), 'back': ('Standing', 0, 'Bip01 Spine2', .8, (0, 1, .15)),
         'shoulder_r': ('Standing', 0, 'Bip01 R UpperArm', .5, (-.8, -.4, .4)), 'shoulder_l': ('Standing', 0, 'Bip01 L UpperArm', .5, (.8, -.4, .4)),
         'fist_r': ('Standing', 0, 'V:Bip01 R Hand', .3, (-.6, -.7, .3)), 'fist_l': ('Standing', 0, 'V:Bip01 L Hand', .3, (.5, -.8, .3)),
         'fist_r_in': ('AttackMelee', 9, 'V:Bip01 R Hand', .3, (.5, -.6, .4)), 'hand_l_cast': ('AttackRanged', 14, 'V:Bip01 L Hand', .32, (.4, -.8, .3)),
         'hips': ('Standing', 0, 'Bip01 Pelvis', .8, (.2, -1, -.1)), 'hips_side': ('Standing', 0, 'Bip01 Pelvis', .8, (-1, -.2, -.05)),
         'legs': ('Standing', 0, 'Bip01 R Calf', .9, (-.3, -1, .1)), 'feet': ('Standing', 0, 'Bip01 R Foot', .6, (-.4, -1, .4)),
         'tail': ('Standing', 0, 'Bip01 Pelvis', 1.0, (.7, .7, .2)), 'cutlass': ('Standing', 0, 'Bone07', .9, (-.8, -.5, .2)),
         'walk': ('Walking', 9, 'Bip01 Spine1', 2.1, (-.6, -.8, .1)), 'attack': ('AttackMelee', 9, 'Bip01 Spine1', 2.2, (-.6, -.8, .2)),
         'pauldron_l_fid2': ('Fidget2', 39, 'Bip01 L UpperArm', .55, (.8, -.3, .3)), 'pauldron_l_fid2b': ('Fidget2', 39, 'Bip01 L UpperArm', .55, (.5, .8, .2)),
         'strap_r_walk': ('Walking', 26, 'Bip01 R Thigh', .55, (-.8, -.5, .1)), 'strap_r_walkb': ('Walking', 26, 'Bip01 R Thigh', .55, (-.6, .8, 0)),
         'bracer_r': ('Standing', 0, 'Bip01 R Forearm', .32, (-.7, -.6, .2)), 'bracer_r_in': ('Standing', 0, 'Bip01 R Forearm', .32, (.4, -.7, -.3)),
         'bracer_l': ('Standing', 0, 'Bip01 L Forearm', .32, (.7, -.6, .2)), 'bracer_l_back': ('Standing', 0, 'Bip01 L Forearm', .32, (.5, .8, .1)),
         'crotch': ('Standing', 0, 'Bip01 Pelvis', .45, (0, -1, -.25)), 'crotch_back': ('Standing', 0, 'Bip01 Pelvis', .45, (0, 1, -.2)),
         'hip_l': ('Standing', 0, 'Bip01 L Thigh', .5, (.9, -.4, .1)), 'pauldron_r_top': ('Standing', 0, 'Bip01 R UpperArm', .55, (-.4, -.3, 1)),
         'hit2': ('Hit2', 15, 'Bip01 Spine1', 2.1, (.6, -.8, .1)), 'death': ('Death', 30, 'Bip01 Pelvis', 2.4, (.6, -.6, .6))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == os.environ.get('MESH', 'LizardOrc'))
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
