"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Griffin (faces -y): head front, three-quarter
and both sides, beak, both wings from above and below, wing tips and feather edges, eagle talons, lion hind paws, tail
tuft, back, belly, Fly down- and up-stroke, Attack and Death; textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are
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
SPOTS = {'head_front': ('Fly', 0, 'Head', .45, (0, -1, .15)), 'head_q34': ('Fly', 0, 'Head', .45, (-.7, -.7, .2)),
         'head_r': ('Fly', 0, 'Head', .5, (-1, 0, .05)), 'head_l': ('Fly', 0, 'Head', .5, (1, 0, .05)),
         'beak': ('Attack', 16, 'Head', .3, (-.8, -.6, -.1)), 'crest': ('Fly', 0, 'Neck2', .55, (0, .4, 1)),
         'wing_l_top': ('Fly', 0, 'Wing2_L', 1.9, (.2, .1, 1)), 'wing_r_top': ('Fly', 0, 'Wing2_R', 1.9, (-.2, .1, 1)),
         'wing_l_under': ('Fly', 0, 'Wing2_L', 1.9, (.3, .1, -1)), 'wing_r_under': ('Fly', 0, 'Wing2_R', 1.9, (-.3, .1, -1)),
         'wing_l_tip': ('Fly', 0, 'Wing3_L', .8, (.3, -.6, .5)), 'wing_r_tip': ('Fly', 0, 'Wing3_R', .8, (-.3, -.6, .5)),
         'talon_l': ('Fly', 0, 'FrontPaw_L', .45, (.5, -.8, .3)), 'talon_r': ('Fly', 0, 'FrontPaw_R', .45, (-.5, -.8, .3)),
         'hpaw_l': ('Fly', 0, 'HindPaw_L', .5, (.7, -.3, .2)), 'hpaw_r': ('Fly', 0, 'HindPaw_R', .5, (-.7, -.3, .2)),
         'tail': ('Fly', 0, 'Tail4', 1.0, (.3, .3, 1)), 'back': ('Fly', 0, 'Spine2', 1.4, (.4, .4, 1)),
         'belly': ('Fly', 0, 'Spine2', 1.6, (.2, 0, -1)), 'flank_r': ('Fly', 0, 'Spine2', 1.8, (-1, 0, .1)),
         'fly_up': ('Fly', 10, 'Spine2', 4.6, (.6, -.7, .4)), 'attack': ('Attack', 16, 'Spine2', 4.0, (-1, -.4, .2)),
         'death': ('Death', 30, 'Spine2', 4.0, (.6, -.6, .6))}
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
