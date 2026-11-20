"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the ground truth for shading and
for each tier (the baked review/viewer tier GLBs). MM7 Devil spots: face, mouth, horns, shoulder spikes, chest, both
clawed hands, the claws in the attack, feet, heel spurs, tail, the corpse. 'V:<group>' frames the centroid of the
posed vertices dominated by that group (the hands reach 60 cm below the wrist).
Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .45, (0, -1, .1)), 'face_q34': ('Standing', 0, 'B_Head', .5, (-.7, -.7, .2)),
         'mouth': ('Standing', 0, 'B_Head', .25, (-.3, -1, -.1)), 'horns_top': ('Standing', 0, 'B_Head', .6, (.2, .3, 1)),
         'shoulders_back': ('Standing', 0, 'B_Spine2', 1.0, (.2, 1, .5)), 'chest': ('Standing', 0, 'B_Spine1', .9, (0, -1, .1)),
         'hand_r': ('Standing', 0, 'V:B_R_Hand', .55, (-.5, -.8, .2)), 'hand_l_in': ('Standing', 0, 'V:B_L_Hand', .55, (-.6, -.6, .1)),
         'claws_attack': ('Attack', 18, 'V:B_R_Hand', .7, (-.5, -.8, .2)), 'foot_r': ('Standing', 0, 'V:B_R_Toe0', .4, (-.6, -.7, .3)),
         'heels_back': ('Standing', 0, 'B_R_Calf', .9, (-.2, 1, .2)), 'tail': ('Standing', 0, 'B_Tail4', 1.3, (-1, .2, .3)),
         'run': ('Running', 6, 'B_Spine1', 2.4, (-1, -.2, .2)), 'death': ('Death', 80, 'B_Pelvis', 2.6, (.6, -.6, .6))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Devil')
    for o in bpy.data.objects:
        if o.type == 'MESH' and o is not body:
            o.hide_render = True
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
