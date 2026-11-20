"""Close-ups of the source and ladder candidates in work/<blend> (default ladder.blend): open-mouth head (Attack at
the 1.25 s release), forefoot and hind foot claws, dorsal spines and tail, wing claw; textured (Eevee) and clay
(workbench + cavity). Writes review/close/<label>_<spot>_<mode>.png and review/close/sheet_<blend stem>.png.
Usage: blender -b -P close_ladder.py -- <blend> <Cand_55,...> [spot,...]"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
blend, cands = args[0], args[1].split(',')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
objs = {'source': bpy.data.objects['Body'], **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in cands}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '420')); sc.render.film_transparent = False
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = 'BOTH'
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
# (action, frame, bone, ortho size, view direction); the Minotaur faces -Y; Attack impact 0.8167 s = frame 19.6
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .5, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .5, (.7, -.7, .1)),
         'face_side': ('Standing', 0, 'B_Head', .5, (1, 0, .05)), 'head_back': ('Standing', 0, 'B_Head', .6, (-.3, 1, .4)),
         'horns': ('Standing', 0, 'B_Head', .75, (.2, -.5, 1)), 'muzzle': ('Standing', 0, 'B_Head', .25, (.5, -.9, -.1)),
         'rhand': ('Standing', 0, 'B_R_Finger2', .3, (-.5, -.8, .2)), 'lhand': ('Standing', 0, 'B_L_Finger2', .3, (.5, -.8, .2)),
         'rhand_back': ('Standing', 0, 'B_R_Hand', .3, (-.6, .7, .3)), 'lhand_back': ('Standing', 0, 'B_L_Hand', .3, (.6, .7, .3)),
         'kilt': ('Standing', 0, 'B_Pelvis', .7, (0, -1, .15)), 'kilt_back': ('Standing', 0, 'B_Pelvis', .7, (0, 1, .15)),
         'chest': ('Standing', 0, 'B_Spine1', .8, (0, -1, .1)), 'back': ('Standing', 0, 'B_Spine1', .9, (0, 1, .3)),
         'legs': ('Standing', 0, 'B_L_Calf', 1.0, (.3, -1, .05)), 'feet': ('Standing', 0, 'B_L_Foot', .45, (.4, -.9, .35)),
         'rfoot': ('Standing', 0, 'B_R_Foot', .45, (-.4, -.9, .35)),
         'nose': ('Standing', 0, 'B_Head', .2, (0, -1, -.05), (0, -.12, -.1)),
         'nose_low': ('Standing', 0, 'B_Head', .2, (.3, -.7, -.65), (0, -.12, -.1)),
         'eye_l': ('Standing', 0, 'B_Head', .14, (.55, -.85, .05), (.06, -.05, 0)),
         'strike': ('Attack', 20, 'B_Spine1', 2.2, (-.6, -.8, .1)), 'death': ('Dead', 0, 'B_Pelvis', 2.4, (.8, -.4, .6))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
# CLOSE_SMOOTH_SRC=1: clear the welded source's custom normals (the weld scrambles them) so clay compares geometry
if os.environ.get('CLOSE_SMOOTH_SRC') == '1':
    s0 = objs['source']; bpy.context.view_layer.objects.active = s0
    with bpy.context.temp_override(object=s0, active_object=s0):
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d, *off) in SPOTS.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = bone(b) + Vector(off[0] if off else (0, 0, 0)); dv = Vector(d).normalized()
    cam.location = c + dv * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = size; cam.data.clip_end = 10
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng
            sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png'); bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
