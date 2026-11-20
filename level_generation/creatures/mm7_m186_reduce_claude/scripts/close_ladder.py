"""Close-ups of the source and ladder candidates in work/<blend> (default ladder.blend): open-mouth head (Attack at
the 1.25 s release), forefoot and hind foot claws, dorsal spines and tail, wing claw; textured (Eevee) and clay
(workbench + cavity). Writes review/close/<label>_<spot>_<mode>.png and review/close/sheet_<blend stem>.png.
Usage: blender -b --factory-startup -P close_ladder.py -- <blend> <Cand_55,...> [spot,...]"""
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
# (action, frame, bone, ortho size, view direction); the dragonfly faces -Y
SPOTS = {'head_side': ('Attack', 13, 'Head', .16, (1, 0, .15)), 'head_front': ('Fly', 0, 'Head', .16, (0, -1, .15)),
         'bristles': ('Fly', 0, 'Head', .14, (.3, -.6, -.7)), 'crest': ('Fly', 0, 'Neck', .28, (1, .3, .4)),
         'claw': ('Fly', 0, 'Claw', .16, (.6, -.8, .2)), 'abdomen': ('Attack', 13, 'Abd5', .4, (1, 0, .2)),
         'back': ('Fly', 0, 'Thorax', .45, (0, 1, .5)), 'wing_top': ('Fly', 0, 'Thorax', 1.0, (0, .15, 1)),
         'wing_front': ('Fly', 0, 'ForeWing_R', .5, (-.3, -1, .2)), 'wing_tip': ('Fly', 0, 'ForeWing_L', .3, (.2, .1, 1)), 'dead': ('Dead', 0, 'Abd3', .6, (.7, -.5, .6))}
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
