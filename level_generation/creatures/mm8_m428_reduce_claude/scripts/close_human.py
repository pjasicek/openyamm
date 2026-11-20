"""Close-ups of the source and ladder candidates (work/<blend>) for the MM8 Dark Elf peasant (faces -y): face front,
three-quarter and side, ear, both hands (Standing grip and Fidget catch), torso front and back, boots, the
Running raised arm and the dress in motion (Running/Walking extremes and front split, Death fall, Dead); textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are rotated by
the weld, so they are cleared here: the installed GLB shades smooth (see glb_close.py).
Usage: blender -b -P close_human.py -- <blend> <Cand_65,...> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
objs = {'source': src, **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in args[1].split(',')}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 10
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '420'))
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .26, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .26, (-.7, -.7, .1)),
         'face_side': ('Standing', 0, 'B_Head', .26, (1, 0, .05)), 'ear': ('Standing', 0, 'B_Head', .2, (-1, .3, .2)),
         'rhand': ('Standing', 0, 'B_R_Hand', .18, (-.5, -.8, .2)), 'lhand': ('Standing', 0, 'B_L_Hand', .18, (.5, -.8, .2)),
         'rhand_fidget': ('Fidget', 40, 'B_R_Hand', .2, (-.3, -1, .3)), 'torso_front': ('Standing', 0, 'B_Spine1', .6, (0, -1, .1)),
         'torso_back': ('Standing', 0, 'B_Spine1', .6, (0, 1, .1)), 'boots': ('Standing', 0, 'B_L_Calf', .6, (-.3, -1, .2)),
         'run_arm': ('Running', 6, 'B_R_UpperArm', .6, (-1, -.4, .2)), 'death': ('Death', 24, 'B_Spine', 1.4, (.6, -.6, .6)),
         'shoulder_l': ('Standing', 0, 'B_L_Clavicle', .32, (.6, -.8, .4)), 'shoulder_r': ('Standing', 0, 'B_R_Clavicle', .32, (-.6, -.8, .4)),
         'neck_v': ('Standing', 0, 'B_Spine1', .32, (0, -1, .15)), 'hem': ('Standing', 0, 'B_Pelvis', .5, (-.3, -1, -.1)),
         'ear_l': ('Standing', 0, 'B_Head', .2, (1, .3, .2)), 'head_back': ('Standing', 0, 'B_Head', .3, (0, 1, .3)),
         'rcuff': ('Standing', 0, 'B_R_Forearm', .25, (-.6, -.8, .1)),
         'lcuff': ('Standing', 0, 'B_L_Forearm', .25, (.6, -.8, .1)), 'rcuff_in': ('Standing', 0, 'B_R_Forearm', .25, (.6, .3, .1)),
         'lcuff_in': ('Standing', 0, 'B_L_Forearm', .25, (-.6, .3, .1)), 'knee_back': ('Standing', 0, 'B_L_Calf', .4, (.2, 1, .1)),
         # dress in motion (m428): extreme Running/Walking frames, the front split, the Death fall and the corpse
         'run_back3': ('Running', 3, 'B_Pelvis', 1.3, (0, 1, .1)), 'run_back9': ('Running', 9, 'B_Pelvis', 1.3, (0, 1, .1)),
         'run_back15': ('Running', 15, 'B_Pelvis', 1.3, (0, 1, .1)), 'run_side9': ('Running', 9, 'B_Pelvis', 1.3, (1, 0, .05)),
         'run_split3': ('Running', 3, 'B_Pelvis', 1.0, (0, -1, 0)), 'run_split15': ('Running', 15, 'B_Pelvis', 1.0, (0, -1, 0)),
         'walk_split6': ('Walking', 6, 'B_Pelvis', 1.0, (0, -1, 0)), 'walk_back16': ('Walking', 16, 'B_Pelvis', 1.3, (.3, 1, .1)),
         'death_fall16': ('Death', 16, 'B_Pelvis', 1.6, (1, -.3, .3)), 'death_fall24': ('Death', 24, 'B_Pelvis', 1.8, (.3, -1, .4)),
         'dead_top': ('Dead', 20, 'B_Pelvis', 1.9, (.2, -.3, 1)), 'dead_under': ('Dead', 20, 'B_Pelvis', 1.9, (1, .2, .15))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in SPOTS.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = bone(b); cam.location = c + Vector(d).normalized() * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
