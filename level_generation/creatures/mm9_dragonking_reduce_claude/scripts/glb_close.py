"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). Dragon King spots: heads, wings (root, knuckles, tip, flap
extremes), body, legs, tail, motion and the corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
# Dragon King spots (glTF +Z faces the camera at (0, -1) after import: Blender -Y front; the demon is ~4 m with 3 m wings).
# Frames are at 30 fps (sc.render.fps before the import): flap down = AttackRanged 2, flap up = Fidget 23 (wing_review.py).
SPOTS = {  # Dragon King (2026-11-05): about 18 units standing, wings to 25; ortho sizes in model units, 30 fps frames
    'head_front': ('Standing', 0, 'Xhead', 6.5, (0, -1, .1)), 'head_q34': ('Standing', 0, 'Xhead', 6.5, (-.7, -.7, .2)),
    'head_profile': ('Standing', 0, 'Xhead', 6.5, (-1, 0, .05)), 'head_low34': ('Standing', 0, 'Xhead', 6.5, (-.7, -.7, -.45)),
    'mouth_open': ('Hit', 12, 'Xhead', 6.5, (-.75, -.6, .1)),
    'body_front': ('Standing', 0, 'Xspine', 30, (0, -1, .1)), 'body_q34': ('Standing', 0, 'Xspine', 30, (-.7, -.7, .2)),
    'body_back': ('Standing', 0, 'Xspine', 30, (0, 1, .15)), 'body_side': ('Standing', 0, 'Xspine', 30, (1, 0, .05)),
    'party': ('Standing', 0, 'Xspine', 60, (-.6, -.8, .15)),
    'wing_root_l': ('Standing', 0, 'Ywarm', 7, (-.3, 1, .4)), 'wing_root_r': ('Standing', 0, 'Ywarm01', 7, (.3, 1, .4)),
    'wing_l_back': ('Standing', 0, 'Yabase', 15, (0, 1, .2)), 'wing_l_front': ('Standing', 0, 'Yabase', 15, (0, -1, .2)),
    'wing_r_back': ('Standing', 0, 'Yabase01', 15, (0, 1, .2)), 'wing_r_front': ('Standing', 0, 'Yabase01', 15, (0, -1, .2)),
    'wing_tip_l': ('Standing', 0, 'Ycpart', 7, (0, 1, .3)), 'wing_tip_r': ('Standing', 0, 'Ycpart01', 7, (0, 1, .3)),
    'flap_down': ('Walking', 12, 'Xspine', 34, (0, 1, .15)), 'flap_up': ('Walking', 30, 'Xspine', 34, (0, 1, .15)),
    'flap_side': ('Walking', 12, 'Xspine', 34, (1, 0, .05)),
    'scales_chest': ('Standing', 0, 'XneckA', 7, (-.3, -1, .1)), 'scales_flank': ('Standing', 0, 'Xspine', 9, (-1, 0, .1)),
    'scales_back': ('Standing', 0, 'XbackA', 9, (0, .7, .8)), 'belly': ('Standing', 0, 'Xspine', 9, (-.2, -.6, -.75)),
    'hindleg': ('Standing', 0, 'Xknee02', 7, (-.6, -.8, .1)), 'foreleg': ('Standing', 0, 'Xelbow02', 7, (-.6, -.8, .1)),
    'tail': ('Standing', 0, 'XtailB', 12, (-.8, .6, .4)),
    'attack': ('AttackMelee', 16, 'Xspine', 34, (-.6, -.8, .2)), 'death': ('Death', 60, 'Xspine', 34, (.6, -.6, .6)),
    'dead': ('Dead', 0, 'Xspine', 34, (.6, -.6, .6))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == os.environ.get('REA_NODE', 'DragonKing'))
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
        cam.location = c + Vector(d).normalized() * float(os.environ.get('DIST', '60')); cam.data.clip_end = 500; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            if mode == 'clay' and os.environ.get('NO_CLAY'):
                continue
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
