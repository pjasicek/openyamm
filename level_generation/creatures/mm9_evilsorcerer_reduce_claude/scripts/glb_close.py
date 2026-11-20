"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). Evil Sorcerer spots: face sheet, crown, chest, pauldrons, belt, panels,
hands, boots, three motion poses, the corpse, full body. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {  # evil sorcerer (1.97 m, faces -y; Blender frames at 24 fps)
    'face_front': ('Standing', 0, 'Bip01 Head', .42, (0, -1, .1)), 'face_q34': ('Standing', 0, 'Bip01 Head', .45, (-.7, -.7, .2)),
    'face_profile': ('Standing', 0, 'Bip01 Head', .45, (-1, 0, .05)), 'face_low34': ('Standing', 0, 'Bip01 Head', .45, (.6, -.7, -.45)),
    'party': ('Standing', 0, 'Bip01 Neck', 1.0, (0, -1, .15)), 'head_back': ('Standing', 0, 'Bip01 Head', .5, (.3, 1, .4)),
    'crown': ('Standing', 0, 'Bip01 Head', .4, (-.4, -1, .9)),
    'chest': ('Standing', 0, 'Bip01 Spine2', .8, (0, -1, .1)), 'back': ('Standing', 0, 'Bip01 Spine2', .9, (0, 1, .15)),
    'shoulder_r': ('Standing', 0, 'Bip01 R UpperArm', .55, (-1, -.4, .3)), 'shoulder_l': ('Standing', 0, 'Bip01 L UpperArm', .55, (1, -.4, .3)),
    'waist': ('Standing', 0, 'Bip01 Pelvis', .9, (.2, -1, .05)), 'waist_back': ('Standing', 0, 'Bip01 Pelvis', .9, (-.2, 1, .05)),
    'legs': ('Standing', 0, 'Bip01 R Calf', 1.2, (-.3, -1, .1)), 'legs_back': ('Standing', 0, 'Bip01 R Calf', 1.2, (.3, 1, .1)),
    'boots': ('Standing', 0, 'Bip01 R Foot', .6, (-.4, -1, .4)),
    'hand_r': ('Standing', 0, 'V:Bip01 R Hand', .3, (-.6, -.7, .3)), 'hand_l': ('Standing', 0, 'V:Bip01 L Hand', .3, (.5, -.8, .3)),
    'walk': ('Walking', 6, 'Bip01 Spine2', 2.4, (-1, -.3, .2)), 'run': ('Running', 6, 'Bip01 Spine2', 2.4, (-.6, -.8, .2)),
    'cast': ('AttackRanged', 20, 'Bip01 Spine2', 2.4, (-.6, -.8, .2)), 'death': ('Death', 24, 'Bip01 Pelvis', 2.6, (.6, -.6, .6)),
    'full_front': ('Standing', 0, 'Bip01 Pelvis', 2.2, (0, -1, .05)), 'full_q34': ('Standing', 0, 'Bip01 Pelvis', 2.2, (-.7, -.7, .1)),
    'full_back': ('Standing', 0, 'Bip01 Pelvis', 2.2, (0, 1, .05)),
    'belt_front': ('Standing', 0, 'V:Bip01 Spine', .45, (.1, -1, .15)), 'belt_back': ('Standing', 0, 'V:Bip01 Spine', .45, (-.1, 1, .15)),
    'belt_side': ('Standing', 0, 'V:Bip01 Spine', .45, (-1, -.2, .1)),
    'panelF_top': ('Standing', 0, 'V:XPanelF1', .4, (.15, -1, .1)), 'panelB_top': ('Standing', 0, 'V:XPanelB1', .4, (-.15, 1, .1)),
    'panelF_hem': ('Standing', 0, 'V:XPanelF4', .45, (.3, -1, .1)), 'panelB_hem': ('Standing', 0, 'V:XPanelB4', .45, (-.3, 1, .1)),
    'flaps_side': ('Standing', 0, 'V:Bip01 R XhalfThigh', .55, (-1, -.3, .1)), 'bracer_r': ('Standing', 0, 'V:Bip01 R Forearm', .4, (-.8, .5, .2)),
    'greave_r': ('Standing', 0, 'V:Bip01 R Calf', .55, (-.5, -1, .2)),
    'panelB_mid': ('Standing', 0, 'V:XPanelB3', .45, (0, 1, .05)), 'panelF_mid': ('Standing', 0, 'V:XPanelF3', .45, (0, -1, .05)),
    'panelB_side': ('Standing', 0, 'V:XPanelB3', .45, (-1, .3, .05)), 'death_panels': ('Death', 24, 'V:XPanelB3', 1.0, (.3, -.3, 1)),
    'walk_lhand': ('Walking', 12, 'V:Bip01 L Hand', .5, (1, -.5, .2)), 'walk_lhand_b': ('Walking', 12, 'V:Bip01 L Hand', .5, (.6, .9, .2)),
    'hit_rhand': ('Hit', 31, 'V:Bip01 R Hand', .5, (-1, -.5, .2)), 'death_rhand': ('Death', 1, 'V:Bip01 R Hand', .5, (-1, -.5, .2)),
    'fidget2_rhand': ('Fidget2', 42, 'V:Bip01 R Hand', .5, (-.3, -1, .2)),
    'death_lhand': ('Death', 9, 'V:Bip01 L Hand', .5, (1, -.5, .4)), 'run_lelbow': ('Running', 8, 'Bip01 L Forearm', .45, (1, -.3, .2)),
    'run_lelbow_in': ('Running', 8, 'Bip01 L Forearm', .45, (-.2, -1, .1)), 'cast_lelbow': ('AttackRanged', 20, 'Bip01 L Forearm', .45, (.8, -.6, .2)),
    'fidget2_relbow': ('Fidget2', 22, 'Bip01 R Forearm', .45, (-.6, -.8, .2)),
    # fix pass: where the MeshLab r75 candidate's UVs escaped (review/uv_audit_f75.json; P: Blender rest-pose point)
    'esc_pauldron_l_front': ('Standing', 0, 'P:0.21,-0.02,1.44', .3, (.4, -1, .2)), 'esc_pauldron_r_front': ('Standing', 0, 'P:-0.21,-0.02,1.44', .3, (-.4, -1, .2)),
    'esc_pauldron_l_back': ('Standing', 0, 'P:0.2,0.12,1.5', .35, (.4, 1, .3)), 'esc_pauldron_r_back': ('Standing', 0, 'P:-0.25,0.11,1.4', .35, (-.4, 1, .3)),
    'esc_hand_l': ('Standing', 0, 'V:Bip01 L Hand', .25, (.9, -.4, .2)), 'esc_hand_r': ('Standing', 0, 'V:Bip01 R Hand', .25, (-.9, -.4, .2)),
    'esc_hand_l_in': ('Standing', 0, 'V:Bip01 L Hand', .25, (-.6, -.7, .2)), 'esc_hand_r_in': ('Standing', 0, 'V:Bip01 R Hand', .25, (.6, -.7, .2)),
    'esc_panelF': ('Standing', 0, 'P:0,-0.13,0.92', .3, (0, -1, .1)), 'esc_bracer_r_back': ('Standing', 0, 'P:-0.36,0.05,1.19', .3, (-.5, 1, .2)),
    'esc_greave_back': ('Standing', 0, 'P:0,0.07,0.41', .7, (0, 1, .15)), 'esc_shoes': ('Standing', 0, 'P:0,-0.05,0.12', .8, (0, -1, .35))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Sorcerer')
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
        if b.startswith('P:'):
            c = Vector([float(x) for x in b[2:].split(',')])
        elif b.startswith('T:'):   # giant: a point on the posed mallet's axis at parameter t (head end negative, as grip_band.py)
            import numpy as np
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
            P = np.array([(body.matrix_world @ m.vertices[i].co)[:] for i, n in enumerate(dom) if n == 'Xhammer']); ev.to_mesh_clear()
            c0 = P.mean(0); ax = np.linalg.svd(P - c0, full_matrices=False)[2][0]; t = (P - c0) @ ax
            r = np.linalg.norm((P - c0) - np.outer(t, ax), axis=1)
            if r[t < 0].max() < r[t > 0].max():
                ax = -ax
            c = Vector((c0 + float(b[2:]) * ax).tolist())
        elif b.startswith('V:'):
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
