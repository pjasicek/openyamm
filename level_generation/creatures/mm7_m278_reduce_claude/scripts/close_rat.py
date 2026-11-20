"""Close-ups of the source and ladder candidates (work/<blend>) for the MM8 Wererat rat form (faces -y): face front,
three-quarter and both sides, ears from above, the Attack bite, all four paws, tail root and tip, back, flank, belly,
Death, Running and Walking; textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are
rotated by the weld, so they are cleared here (judge final shading from GLBs, glb_close.py).
Usage: blender -b -P close_rat.py -- <blend> <Cand_75,...> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
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
SPOTS = {'face_front': ('Standing', 0, 'Head', .2, (0, -1, .15)), 'face_q34': ('Standing', 0, 'Head', .2, (-.7, -.7, .2)),
         'face_r': ('Standing', 0, 'Head', .22, (-1, 0, .05)), 'face_l': ('Standing', 0, 'Head', .22, (1, 0, .05)),
         'ears': ('Standing', 0, 'Head', .18, (0, .4, 1)), 'bite': ('Attack', 16, 'Head', .22, (-.7, -.7, 0)),
         'fpaw_r': ('Standing', 0, 'FrontPaw_R', .12, (-.5, -.8, .3)), 'fpaw_l': ('Standing', 0, 'FrontPaw_L', .12, (.5, -.8, .3)),
         'hpaw_r': ('Standing', 0, 'HindPaw_R', .14, (-.7, -.5, .3)), 'hpaw_l': ('Standing', 0, 'HindPaw_L', .14, (.7, -.5, .3)),
         'tail_root': ('Standing', 0, 'Tail1', .3, (1, .3, .3)), 'tail_tip': ('Standing', 0, 'Tail5', .35, (.3, .2, 1)),
         'back': ('Standing', 0, 'Spine2', .55, (.4, .2, 1)), 'flank_r': ('Standing', 0, 'Spine2', .55, (-1, 0, .1)),
         'belly': ('Standing', 0, 'Spine2', .55, (.3, 0, -1)), 'death': ('Death', 18, 'Spine2', .8, (.6, -.6, .6)),
         'run': ('Running', 6, 'Spine2', .7, (-1, -.3, .2)), 'walk': ('Walking', 15, 'Spine2', .7, (1, -.3, .2)),
         'mouth_side': ('Standing', 0, 'Jaw', .09, (-1, -.3, 0)), 'mouth_front': ('Standing', 0, 'Jaw', .09, (0, -1, .1)),
         'mouth_open': ('Attack', 16, 'Jaw', .1, (-.8, -.6, -.1)), 'mouth_open_l': ('Attack', 16, 'Jaw', .1, (.8, -.6, -.1)),
         'soles': ('Standing', 0, 'Spine2', .6, (.1, .1, -1))}
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
