"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). MM7 Devil spots: face, mouth, horns, shoulder spikes, chest, both
clawed hands, the claws in the attack, feet, heel spurs, tail, the corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {  # giant (2.56 m, faces -y; Blender frames at 24 fps)
    'face_front': ('Standing', 0, 'Bip01 Head', .45, (0, -1, .1)), 'face_q34': ('Standing', 0, 'Bip01 Head', .5, (-.7, -.7, .2)),
    'face_profile': ('Standing', 0, 'Bip01 Head', .5, (-1, 0, .05)), 'face_low34': ('Standing', 0, 'Bip01 Head', .5, (.6, -.7, -.45)),
    'party': ('Standing', 0, 'Bip01 Neck', 1.1, (0, -1, .15)), 'head_back': ('Standing', 0, 'Bip01 Head', .6, (.3, 1, .4)),
    'chest': ('Standing', 0, 'Bip01 Spine2', 1.0, (0, -1, .1)), 'back': ('Standing', 0, 'Bip01 Spine2', 1.1, (0, 1, .15)),
    'loin': ('Standing', 0, 'Bip01 Pelvis', 1.1, (.2, -1, -.05)), 'loin_back': ('Standing', 0, 'Bip01 Pelvis', 1.1, (-.2, 1, -.05)),
    'legs': ('Standing', 0, 'Bip01 R Calf', 1.3, (-.3, -1, .1)), 'boots': ('Standing', 0, 'Bip01 R Foot', .8, (-.4, -1, .4)),
    'fist_r': ('Standing', 0, 'V:Bip01 R Hand', .45, (-.6, -.7, .3)), 'fist_l': ('Standing', 0, 'V:Bip01 L Hand', .45, (.5, -.8, .3)),
    'mallet': ('Standing', 0, 'Xhammer', 1.6, (0, -1, .25)), 'mallet_head': ('Standing', 0, 'V:Xhammer', 1.4, (.3, -1, .3)),
    'walk': ('Walking', 6, 'Bip01 Spine2', 3.0, (-1, -.3, .2)), 'attack': ('AttackMelee', 12, 'Bip01 Spine2', 3.4, (-.6, -.8, .2)),
    'death': ('Death', 70, 'Bip01 Pelvis', 3.6, (.6, -.6, .6)), 'hit2_back': ('Hit2', 12, 'Bip01 Spine2', 1.2, (.2, 1, .2)),
    'mallet_neck': ('Standing', 0, 'T:-0.15', .45, (.2, -1, .3)), 'mallet_hd': ('Standing', 0, 'T:-0.44', .6, (.4, -1, .4)),
    'mallet_hd_back': ('Standing', 0, 'T:-0.44', .6, (-.4, 1, .2)), 'pommel': ('Standing', 0, 'T:0.9', .4, (.2, -1, .3)),
    'pommel_att': ('AttackMelee', 14, 'T:0.82', .7, (.3, -1, .2)), 'pommel_att2': ('AttackMelee', 14, 'T:0.82', .7, (-1, .3, .3)),
    'pommel_att3': ('AttackMelee', 11, 'T:0.82', .7, (.3, -1, .2))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Giant')
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
        if b.startswith('T:'):   # giant: a point on the posed mallet's axis at parameter t (head end negative, as grip_band.py)
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
