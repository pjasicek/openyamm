"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Genie (faces -y, 1.79 m): face, earrings, ponytail,
folded arms and both hands, the raised hands of the cast, collar, top from behind, the vortex, Attack, Walking, Death
and Hit; textured (Eevee) and clay
(workbench + cavity). The welded source's custom normals are rotated by the weld, so they are cleared here (judge
final shading from GLBs, glb_close.py).
Usage: blender -b -P close_m162.py -- <blend> <Cand_75,...> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
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
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .45, (0, -1, .1)), 'face_q34': ('Standing', 0, 'B_Head', .45, (-.7, -.7, .15)),
         'face_l': ('Standing', 0, 'B_Head', .5, (1, 0, .05)), 'earring': ('Standing', 0, 'B_Head', .3, (.6, -.8, -.4)),
         'pony_back': ('Standing', 0, 'B_Head', .75, (.3, 1, .4)), 'pony_side': ('Standing', 0, 'B_Head', .75, (-1, .1, .2)),
         'arms_folded': ('Standing', 0, 'B_Spine2', .75, (0, -1, .1)), 'hand_r': ('Standing', 0, 'B_R_Hand', .35, (-.4, -.9, .3)),
         'hand_l': ('Standing', 0, 'B_L_Hand', .35, (.4, -.9, .3)), 'hands_up': ('Attack', 24, 'B_R_Hand', .7, (0, -1, .2)),
         'collar': ('Standing', 0, 'B_Neck', .45, (0, -1, .3)), 'top_back': ('Standing', 0, 'B_Spine2', .7, (0, 1, .2)),
         'vortex_side': ('Standing', 0, 'Vortex_03', 1.25, (-1, 0, .1)), 'vortex_q34': ('Standing', 0, 'Vortex_03', 1.25, (.7, -.7, .3)),
         'attack': ('Attack', 24, 'B_Spine1', 2.2, (-.7, -.7, .3)), 'walk': ('Walking', 14, 'B_Spine1', 2.2, (1, -.3, .2)),
         'death': ('Death', 24, 'B_Spine1', 2.4, (.6, -.6, .4)), 'hit': ('Hit', 6, 'B_Spine1', 2.2, (0, -1, .2)),
         'hair_top': ('Standing', 0, 'B_Head', .35, (0, -.4, 1)), 'hair_back': ('Standing', 0, 'B_Head', .35, (0, 1, .3)),
         'chest': ('Standing', 0, 'B_Spine1', .4, (0, -1, .1))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in SPOTS.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = bone(b); cam.location = c + Vector(d).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
