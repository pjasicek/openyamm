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
# (action, frame, bone, ortho size, view direction); the dragon faces -Y
SPOTS = {'mouth_side': ('Attack', 30, 'Head', .22, (1, 0, .15)), 'mouth_q34': ('Attack', 30, 'Head', .22, (.6, -.8, .35)),
         'head_front': ('Standing', 0, 'Head', .22, (0, -1, .15)), 'head_top': ('Standing', 0, 'Head', .22, (.1, -.3, 1)),
         'forefoot': ('Standing', 0, 'RForeFoot', .12, (-.6, -.8, .1)), 'hindfoot': ('Standing', 0, 'RHindFoot', .14, (-.7, -.7, .1)),
         'spines': ('Standing', 0, 'Spine2', .4, (1, .1, .5)), 'tail': ('Standing', 0, 'Tail6', .4, (1, 0, .6)),
         'wing': ('Standing', 0, 'RWing2', .45, (-.2, -1, .3)), 'belly': ('Standing', 0, 'Spine1', .4, (.3, -.3, -1)),
         'lwing_out': ('Standing', 0, 'LWing2', .42, (1, .15, .1)), 'rwing_out': ('Standing', 0, 'RWing2', .42, (-1, .15, .1)),
         'lwing_in': ('Standing', 0, 'LWing2', .42, (-1, -.15, .1)), 'flank_l': ('Standing', 0, 'Spine1', .5, (1, 0, .05)),
         'flank_r': ('Standing', 0, 'Spine1', .5, (-1, 0, .05))}
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
