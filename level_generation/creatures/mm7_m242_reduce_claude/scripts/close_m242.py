"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Ghost (faces -y, 1.86 m): skull front,
three-quarter and side, hood from behind and in the Fidget, ribs, both claw hands, robe shreds front and back, Attack,
Walking, Death and the Dead heap; textured (Eevee) and clay
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
SPOTS = {'skull_front': ('Standing', 0, 'B_Head', .45, (0, -1, .1)), 'skull_q34': ('Standing', 0, 'B_Head', .45, (-.7, -.7, .15)),
         'skull_side': ('Standing', 0, 'B_Head', .5, (-1, 0, .05)), 'hood_back': ('Standing', 0, 'B_Head', .8, (.1, 1, .4)),
         'hood_fidget': ('Fidget', 42, 'B_Head', .9, (-.6, -.7, .3)), 'ribs': ('Standing', 0, 'B_Spine1', .7, (0, -1, .05)),
         'hand_r': ('Standing', 0, 'B_R_Hand', .4, (-.5, -.8, .3)), 'hand_l': ('Standing', 0, 'B_L_Hand', .4, (.5, -.8, .3)),
         'attack': ('Attack', 30, 'B_Spine1', 2.0, (-.7, -.7, .3)), 'shreds_front': ('Standing', 0, 'B_Pelvis', 1.4, (0, -1, 0)),
         'shreds_back': ('Standing', 0, 'B_Pelvis', 1.4, (.2, 1, .1)), 'walk': ('Walking', 12, 'B_Spine1', 2.2, (-1, -.2, .2)),
         'death': ('Death', 52, 'B_Pelvis', 2.2, (.6, -.6, .6)), 'dead_top': ('Dead', 0, 'B_Pelvis', 2.2, (0, -.2, 1))}
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
