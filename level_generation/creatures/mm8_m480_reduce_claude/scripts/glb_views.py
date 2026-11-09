"""Troll Peasant close-ups (copied from the Troll m476; the peasant holds its club in the right hand) straight from GLBs (their own normals, no weld): face, mouth, hair, both hands with the club,
torso, boots, the attack wind-up from below and Death; textured (Eevee) and clay (workbench).
Usage: blender -b -P glb_views.py -- <out dir> <label=glb,...> [spot,...]  -> <out>/<label>_<spot>_<mode>.png"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(HERE, args[0]); os.makedirs(out, exist_ok=True)
# (action, frame, bone, ortho size, view direction); the Troll faces -Y, its left side is +X
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .34, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .34, (.7, -.7, .15)),
         'face_side': ('Standing', 0, 'B_Head', .34, (1, 0, .05)), 'mouth': ('Standing', 0, 'B_Head', .2, (.15, -1, -.15)),
         'hair_back': ('Standing', 0, 'B_Head', .4, (-.3, 1, .4)), 'club_hand': ('Standing', 0, 'B_R_Hand', .32, (-.8, -.6, .2)),
         'club_hand_in': ('Standing', 0, 'B_R_Hand', .32, (.6, -.8, .1)), 'left_hand': ('Standing', 0, 'B_L_Hand', .3, (.8, -.6, .2)),
         'torso_front': ('Standing', 0, 'B_Spine', .9, (0, -1, .1)), 'torso_back': ('Standing', 0, 'B_Spine', .9, (0, 1, .1)),
         'boots': ('Standing', 0, 'B_L_Foot', .45, (.5, -.85, .25)), 'windup_below': ('Attack', 18, 'B_R_UpperArm', .7, (-.3, -.6, -.75)),
         'windup': ('Attack', 18, 'B_Spine', 1.5, (.7, -.7, .2)), 'death': ('Death', 31, 'B_Pelvis', 1.8, (1, -.3, .7)),
         'hair_top': ('Standing', 0, 'B_Head', .4, (.1, .2, 1)), 'hair_side': ('Standing', 0, 'B_Head', .4, (1, .3, .2)),
         **{f'feet_{c.lower()}{fr}_{v}': (c, fr, 'FEET', 1.0, d) for c, fr in (('Standing', 0), ('Fidget', 30), ('Hit', 3),
            ('Attack', 20), ('Walking', 6), ('Walking', 18)) for v, d in (('front', (0, -1, .08)), ('side', (1, 0, .08)))},
         'skull_side': ('Standing', 0, 'CLUBHEAD', .42, (1, 0, .1)), 'skull_front': ('Standing', 0, 'CLUBHEAD', .42, (0, -1, .1)),
         'skull_back': ('Standing', 0, 'CLUBHEAD', .42, (-.6, .8, .2)), 'skull_top': ('Standing', 0, 'CLUBHEAD', .42, (.2, -.2, 1))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
for item in args[1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 20; sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RES', '420'))
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    if any(v[2] == 'FEET' for v in SPOTS.values()):  # a floor at height 0 for the feet views
        bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0)); fl = bpy.context.object
        m = bpy.data.materials.new('Floor'); m.use_nodes = True
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.12, .14, .18, 1); fl.data.materials.append(m)
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
        if b == 'FEET':  # both feet, at sole height (camera just above the floor)
            pts = [rig.matrix_world @ rig.pose.bones[f'B_{s}_Foot'].head for s in 'LR']
            c = (pts[0] + pts[1]) / 2; c.z = .12
        elif b == 'CLUBHEAD':  # the skull end of the merged review club (club-space z above 0.38)
            club = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('ClubReview'))
            pts = [club.matrix_world @ v.co for v in club.data.vertices if v.co.z > .38]
            c = sum(pts, Vector()) / len(pts)
        else:
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            if os.environ.get('MODES') and mode not in os.environ['MODES']:
                continue
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBVIEWS done')
