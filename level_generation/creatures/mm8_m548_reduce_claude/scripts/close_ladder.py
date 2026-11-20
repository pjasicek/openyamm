"""Close-ups of the source and ladder candidates in work/<blend> (default ladder.blend): head and crown, open mouth
(Attack release), fore and hind claws, dorsal ridge, tail spikes and the corpse; textured (Eevee) and clay
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
# (action, frame, bone, ortho size, view direction); the Crystal Dragon faces -Y, Attack releases at 0.375 s (frame 9)
SPOTS = {'head_front': ('Standing', 0, 'Head', .34, (0, -1, .1)), 'head_q34': ('Standing', 0, 'Head', .34, (.7, -.7, .15)),
         'head_side': ('Standing', 0, 'Head', .34, (1, 0, .1)), 'crown': ('Standing', 0, 'Head', .4, (-.3, .5, .9)),
         'mouth': ('Attack', 9, 'Head', .34, (.7, -.7, .1)), 'forepaw': ('Standing', 0, 'FrontPaw_L', .22, (.6, -.8, .3)),
         'hindpaw': ('Standing', 0, 'HindPaw_R', .22, (-.6, -.8, .3)), 'dorsal': ('Standing', 0, 'Spine2', .6, (1, 0, .4)),
         'tail': ('Standing', 0, 'Tail2', .4, (.6, .8, .4)), 'dead': ('Dead', 0, 'Spine1', 1.0, (.8, -.4, .6))}
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
# CLOSE_SMOOTH_SRC=1: clear the welded source's custom normals (the weld scrambles them) so clay compares geometry
if os.environ.get('CLOSE_SMOOTH_SRC') == '1':
    s0 = objs['source']; bpy.context.view_layer.objects.active = s0
    with bpy.context.temp_override(object=s0, active_object=s0):
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
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
