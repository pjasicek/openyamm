"""Close-ups of the source and ladder candidates in work/<blend> (default ladder.blend): head, open mouth at
the strike, both three-claw hands, torso front and back, tail, tail tip and corpse; textured (Eevee) and clay
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
# (action, frame, bone, ortho size, view direction); the Serpentman faces -Y, the strike lands at Attack frame 18
SPOTS = {'head_front': ('Standing', 0, 'Head', .3, (0, -1, .1)), 'head_side': ('Standing', 0, 'Head', .3, (1, -.1, .1)),
         'mouth': ('Attack', 18, 'Head', .3, (.6, -.8, .2)), 'mouth_low': ('Attack', 18, 'Jaw', .25, (.2, -.8, -.5)),
         'hand_r': ('Standing', 0, 'R_Digit1_1', .3, (-.5, -.8, .4)), 'hand_l': ('Attack', 18, 'L_Digit1_1', .3, (.5, -.8, .4)),
         'palm_r': ('Standing', 0, 'R_Digit1_0', .3, (.3, -.6, -.7)),
         'torso': ('Standing', 0, 'Spine_05', .9, (.3, -1, .1)), 'back': ('Standing', 0, 'Spine_05', .9, (0, 1, .3)),
         'tail': ('Standing', 0, 'Tail_12', 2.4, (.2, .2, 1)), 'tail_tip': ('Standing', 0, 'Tail_24', .9, (.6, .3, 1)),
         'dead': ('Dead', 0, 'Spine_03', 2.2, (.7, -.5, .6))}
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
