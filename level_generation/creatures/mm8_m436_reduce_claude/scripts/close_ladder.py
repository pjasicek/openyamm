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
SPOTS = {'head_front': ('Standing', 0, 'B_Head', .32, (0, -1, .1)), 'head_side': ('Standing', 0, 'B_Head', .32, (1, -.2, .1)),
         'head_back': ('Standing', 0, 'B_Head', .32, (-.3, 1, .4)),
         'hand_l': ('Standing', 0, 'B_L_Finger21', .26, (.5, -.8, .1)), 'hand_r': ('Standing', 0, 'B_R_Finger21', .26, (-.5, -.8, .1)),
         'palm_l': ('Standing', 0, 'B_L_Finger21', .26, (-.6, .2, -.2)), 'palm_r': ('Standing', 0, 'B_R_Finger21', .26, (.6, .2, -.2)),
         'feet': ('Standing', 0, 'B_Pelvis', .9, (.3, -1, -.05)), 'feet_close': ('Standing', 0, 'B_R_Toe0', .3, (-.3, -1, .6)), 'feet_l': ('Standing', 0, 'B_L_Toe0', .3, (.5, -1, .6)),
         'toes_top': ('Standing', 0, 'B_R_Toe0', .3, (0, -.3, 1)), 'heel': ('Standing', 0, 'B_L_Foot', .3, (.5, 1, .3)),
         'shorts': ('Walking', 12, 'B_Pelvis', .7, (.2, -1, .1)), 'torso': ('Standing', 0, 'B_Spine1', .8, (.3, -1, .1)),
         'pack': ('Standing', 0, 'B_Spine2', .8, (-.4, 1, .2)), 'side': ('Standing', 0, 'B_Spine', 1.8, (1, 0, .05)),
         'corpse': ('Dead', 0, 'B_Spine1', 1.9, (.7, -.7, .6))}
# the welded source keeps custom normals stored relative to the old default normals (scrambled by the weld): drop them so
# source and candidates shade from their geometry alike; judge final shading from GLB renders
src_me = objs['source'].data
if src_me.has_custom_normals:
    src_me.free_normals_split() if hasattr(src_me, 'free_normals_split') else None
    bpy.context.view_layer.objects.active = objs['source']; bpy.ops.mesh.customdata_custom_splitnormals_clear()
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
