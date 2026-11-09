"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). Greater Demon spots: heads, wings (root, knuckles, tip, flap
extremes), body, legs, tail, motion and the corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
# Greater Demon spots (glTF +Z faces the camera at (0, -1) after import: Blender -Y front; the demon is ~4 m with 3 m wings).
# Frames are at 30 fps (sc.render.fps before the import): flap down = AttackRanged 2, flap up = Fidget 23 (wing_review.py).
SPOTS = {'face_front': ('Standing', 0, 'Xhead', .95, (0, -1, .1)), 'face_q34': ('Standing', 0, 'Xhead', 1.0, (-.7, -.7, .2)),
         'face_profile': ('Standing', 0, 'Xhead', 1.0, (-1, 0, .05)),
         'armhead_l': ('Standing', 0, 'Xahead', .8, (-.5, -.8, .3)), 'armhead_r': ('Standing', 0, 'Xahead01', .8, (.5, -.8, .3)),
         'body_front': ('Standing', 0, 'XspineA', 4.6, (0, -1, .1)), 'body_q34': ('Standing', 0, 'XspineA', 4.6, (-.7, -.7, .2)),
         'body_back': ('Standing', 0, 'XspineA', 4.6, (0, 1, .15)), 'wing_q34b': ('Standing', 0, 'XwingA', 2.6, (.8, .9, .35)),
         'wing_root': ('Standing', 0, 'Xwing', 1.1, (-.4, 1, .45)), 'wing_knuckles': ('Standing', 0, 'XwingB', 1.3, (-.5, .9, .3)),
         'wing_tip': ('Standing', 0, 'XwingD', 1.4, (-.4, 1, .2)), 'wing_front': ('Standing', 0, 'XwingB', 2.6, (-.3, -1, .3)),
         'flap_down': ('AttackRanged', 2, 'XspineB', 4.6, (0, 1, .15)), 'flap_up': ('Fidget', 23, 'XspineB', 4.8, (0, 1, .15)),
         'flap_up_side': ('Fidget', 23, 'XspineB', 4.8, (1, 0, .05)),
         'chest': ('Standing', 0, 'XspineB', 1.6, (-.4, -1, .1)), 'arm_l': ('Standing', 0, 'Xaelbow', 1.6, (-.4, -1, .3)),
         'legs': ('Standing', 0, 'Xlegmid', 1.8, (-.6, -.8, .1)), 'tail': ('Standing', 0, 'XtailB', 2.0, (-.8, .6, .4)),
         'walk': ('Walking', 10, 'XspineA', 4.6, (-.6, -.8, .1)), 'attack': ('AttackMelee', 12, 'XspineA', 4.6, (-.6, -.8, .2)),
         'death': ('Death', 50, 'XspineA', 4.8, (.6, -.6, .6)), 'dead': ('Dead', 0, 'XspineA', 4.8, (.6, -.6, .6)),
         # the h85 candidate's three escaping membrane faces (reduction_uv_audit.py, glTF bind positions -> Blender (x, -z, y)),
         # in the bind pose, seen along their normals from both sides of the shell
         'esc_tip_out': ('REST', 0, 'P:-1.60,2.21,3.24', .45, (-.855, -.518, -.018)),
         'esc_tip_in': ('REST', 0, 'P:-1.60,2.21,3.24', .45, (.855, .518, .018)),
         'esc_root_out': ('REST', 0, 'P:-0.49,0.86,2.65', .45, (-.942, -.332, -.041)),
         'esc_root_in': ('REST', 0, 'P:-0.49,0.86,2.65', .45, (.942, .332, .041)),
         'membrane_l_back': ('REST', 0, 'P:-1.1,1.4,3.0', 2.2, (-.3, 1, .2)), 'membrane_l_front': ('REST', 0, 'P:-1.1,1.4,3.0', 2.2, (-.3, -1, .2))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == os.environ.get('REA_NODE', 'GreaterDemon'))
    vg = {g.index: g.name for g in body.vertex_groups}
    dom = [vg[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in body.data.vertices]
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RES', '420'))
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    for spot, (act, frame, b, size, d) in SPOTS.items():
        if act == 'REST':
            rig.animation_data.action = None
            for pb_ in rig.pose.bones:
                pb_.matrix_basis.identity()
            bpy.context.view_layer.update()
        else:
            rig.animation_data.action = bpy.data.actions[act]
            if bpy.data.actions[act].slots:
                rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
            sc.frame_set(frame)
        if b.startswith('P:'):
            c = Vector([float(x) for x in b[2:].split(',')])
        elif b.startswith('V:'):
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
            ids = [i for i, n in enumerate(dom) if n == b[2:]]
            c = sum((body.matrix_world @ m.vertices[i].co for i in ids), Vector()) / len(ids); ev.to_mesh_clear()
        else:
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * (1.5 if b.startswith('P:') else 6); cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            if mode == 'clay' and os.environ.get('NO_CLAY'):
                continue
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
