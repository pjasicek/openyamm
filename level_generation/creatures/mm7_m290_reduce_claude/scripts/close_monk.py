"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Monk (faces -y): face in the hood, hood
tip and back, cowl, folded arms, sleeves in Attack/Cast, hands, rope, hem, sandals, back and Death; textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are rotated by
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
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .3, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .3, (-.7, -.7, .1)),
         'hood_side': ('Standing', 0, 'B_Head', .55, (1, 0, .1)), 'hood_back': ('Standing', 0, 'B_Neck', .6, (0, 1, .3)),
         'cowl_front': ('Standing', 0, 'B_Spine2', .6, (.3, -1, .3)), 'folded': ('Standing', 0, 'B_Spine1', .6, (0, -1, .1)),
         'folded_q34': ('Walking', 8, 'B_Spine1', .6, (-.7, -.7, .1)), 'sleeve_attack': ('Attack', 13, 'B_R_Forearm', .6, (-.5, -.8, .2)),
         'sleeve_cast': ('Cast', 14, 'B_L_Forearm', .6, (.5, -.8, .2)), 'hand_cast': ('Cast', 14, 'B_R_Hand', .25, (-.4, -.9, .2)),
         'hand_fidget': ('Fidget', 24, 'B_L_Hand', .25, (.3, -1, .2)), 'rope': ('Standing', 0, 'B_Pelvis', .55, (.2, -1, 0)),
         'hem': ('Standing', 0, 'B_L_Calf', .7, (-.3, -1, -.1)), 'feet': ('Walking', 6, 'B_L_Foot', .45, (-.5, -.8, .1)),
         'back': ('Standing', 0, 'B_Spine', .9, (0, 1, .1)), 'death': ('Death', 30, 'B_Spine', 1.6, (.6, -.6, .6))}
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
