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
# (action, frame, bone, ortho size, view direction); the Water Elemental faces -Y; Attack 21 = 0.875 s release
SPOTS = {'mouth_side': ('Attack', 21, 'Head', .35, (1, 0, .15)), 'mouth_q34': ('Attack', 21, 'Head', .35, (.6, -.8, .35)),
         'head_front': ('Standing', 0, 'Head', .35, (0, -1, .15)), 'head_top': ('Standing', 0, 'Head', .35, (.1, -.3, 1)),
         'teeth_front': ('Attack', 21, 'Jaw', .16, (.2, -1, .2)), 'hand_l': ('Standing', 0, 'L_Hand', .3, (.6, -.8, .2)),
         'hand_r': ('Standing', 0, 'R_Hand', .3, (-.6, -.8, .2)), 'forearm_fin': ('Standing', 0, 'L_Forearm', .45, (1, -.2, .3)),
         'sail': ('Standing', 0, 'Spine_04', .8, (1, 0, .3)), 'tail_fin': ('Standing', 0, 'Tail_07', .6, (1, -.2, .4)),
         'tail_fin_r': ('Standing', 0, 'Tail_07', .6, (-1, -.2, .4)), 'caudal': ('Standing', 0, 'Caudal', .6, (1, 0, .5)),
         'tail_top': ('Standing', 0, 'Tail_12', 1.6, (.2, 0, 1)), 'belly': ('Standing', 0, 'Spine_02', .8, (.3, -1, 0)),
         'back': ('Standing', 0, 'Spine_03', 1.0, (0, .7, .7)), 'corpse': ('Dead', 0, 'Spine_02', 1.8, (.7, -.7, .6)),
         'corpse_low': ('Dead', 0, 'Tail_04', .8, (1, -.3, .3))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in SPOTS.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = bone(b); dv = Vector(d).normalized()
    cam.location = c + dv * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = size; cam.data.clip_end = 10
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng
            sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png'); bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
