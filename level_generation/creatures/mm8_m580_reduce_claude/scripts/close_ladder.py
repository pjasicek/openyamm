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
# (action, frame, bone, ortho size, view direction); the turtle faces -Y; Bite contact at 0.75 s = frame 18
SPOTS = {'mouth_side': ('Bite', 14, 'Head', .3, (1, 0, .15)), 'mouth_q34': ('Bite', 14, 'Head', .3, (.6, -.8, .35)),
         'head_front': ('SwimIdle', 0, 'Head', .3, (0, -1, .15)), 'head_top': ('SwimIdle', 0, 'Head', .3, (.1, -.3, 1)),
         'front_paddle': ('SwimIdle', 0, 'Front_R', .55, (-.2, -.2, 1)), 'front_under': ('SwimIdle', 0, 'Front_R', .55, (-.2, -.2, -1)),
         'rear_paddle': ('SwimIdle', 0, 'Rear_R', .4, (-.3, .3, 1)), 'tail': ('SwimIdle', 0, 'Tail2', .4, (1, .2, .5)),
         'shell_top': ('SwimIdle', 0, 'Shell', 1.1, (.1, -.15, 1)), 'shell_side': ('SwimIdle', 0, 'Shell', 1.1, (1, 0, .1)),
         'belly': ('SwimIdle', 0, 'Shell', 1.1, (.1, -.2, -1)), 'neck': ('SwimIdle', 0, 'Neck2', .45, (-1, -.3, .2)),
         'mouth_zoom': ('Bite', 14, 'Jaw', .16, (.7, -.7, .2)), 'mouth_front': ('Bite', 14, 'Jaw', .16, (0, -1, .1)),
         'rear_zoom': ('SwimIdle', 0, 'RearTip_R', .22, (-.2, .2, 1)), 'front_rim': ('SwimIdle', 0, 'FrontTip_R', .3, (-.2, -.1, 1))}
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
