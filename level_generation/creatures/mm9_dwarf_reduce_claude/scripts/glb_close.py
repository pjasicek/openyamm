"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). Dwarf spots: the face sheet (front, 3/4, profile, low 3/4, party), chest,
back, boots, both fists, attack, corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {  # dwarf (1.33 m, faces -y; Blender frames at 30 fps here); face sheet of the brief plus the cut regions
    'face_front': ('Standing', 0, 'Bip01 Head', .32, (0, -1, .05)), 'face_q34': ('Standing', 0, 'Bip01 Head', .36, (-.7, -.7, .15)),
    'face_profile': ('Standing', 0, 'Bip01 Head', .38, (-1, 0, .02)), 'face_low34': ('Standing', 0, 'Bip01 Head', .38, (.6, -.7, -.5)),
    'party': ('Standing', 0, 'Bip01 Neck', .8, (0, -1, .15)), 'head_back': ('Standing', 0, 'Bip01 Head', .42, (.3, 1, .4)),
    'chest': ('Standing', 0, 'Bip01 Spine1', .6, (0, -1, .1)), 'back': ('Standing', 0, 'Bip01 Spine1', .65, (0, 1, .15)),
    'boots': ('Standing', 0, 'Bip01 R Calf', .55, (-.4, -1, .3)),
    'fist_r': ('Standing', 0, 'V:Bip01 R Hand', .25, (-.6, -.7, .3)), 'fist_l': ('Standing', 0, 'V:Bip01 L Hand', .25, (.5, -.8, .3)),
    # fix pass: where the MeshLab candidate's faces left the painted charts (review/uv_audit_e71.json): sleeves and upper
    # arms (|x| 0.24-0.39 m, both sides, front and back) and the back of the boot shafts/calves
    'arm_r_out': ('Standing', 0, 'Bip01 R UpperArm', .5, (-1, -.2, .1)), 'arm_l_out': ('Standing', 0, 'Bip01 L UpperArm', .5, (1, -.2, .1)),
    'arm_r_back': ('Standing', 0, 'Bip01 R UpperArm', .5, (-.5, 1, .15)), 'arm_l_back': ('Standing', 0, 'Bip01 L UpperArm', .5, (.5, 1, .15)),
    'arm_r_front': ('Standing', 0, 'Bip01 R UpperArm', .5, (-.4, -1, .1)), 'calves_back': ('Standing', 0, 'Bip01 Spine', .7, (0, 1, -.35)),
    'attack': ('AttackMelee', 15, 'Bip01 Spine1', 1.6, (-.6, -.8, .2)), 'death': ('Death', 42, 'Bip01 Spine', 1.8, (.6, -.6, .6))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Dwarf')
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
