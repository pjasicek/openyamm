"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Warlock (faces -y; added spots death8/16, dead, walk, walk_back, cast, bodice, hair_back, cape_side), first written for the MM8 Cleric: face, hair,
collar, both hands (staff grip, Cast), torso, sash, hem, feet, cuffs, shoulders, Death and Attack; textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are rotated by
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
if os.environ.get('CULL') == '1':                  # engine view: single-sided triangles are back-face culled
    for m in bpy.data.materials:
        m.use_backface_culling = True
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
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .26, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .26, (-.7, -.7, .1)),
         'face_side': ('Standing', 0, 'B_Head', .26, (1, 0, .05)), 'head_back': ('Standing', 0, 'B_Head', .34, (0, 1, .3)),
         'hair_side': ('Standing', 0, 'B_Neck', .4, (-1, .2, .1)), 'collar_front': ('Standing', 0, 'B_Neck', .5, (.3, -1, .2)),
         'collar_back': ('Standing', 0, 'B_Neck', .5, (-.2, 1, .3)), 'rhand': ('Standing', 0, 'B_R_Hand', .2, (-.5, -.8, .2)),
         'lhand': ('Standing', 0, 'B_L_Hand', .2, (.5, -.8, .2)), 'lhand_cast': ('Cast', 30, 'B_L_Hand', .24, (.2, -1, .3)),
         'torso_front': ('Standing', 0, 'B_Spine1', .6, (0, -1, .1)), 'torso_back': ('Standing', 0, 'B_Spine1', .6, (0, 1, .1)),
         'sash': ('Standing', 0, 'B_Pelvis', .6, (.2, -1, 0)), 'hem': ('Standing', 0, 'B_L_Calf', .7, (-.3, -1, -.1)),
         'hem_back': ('Walking', 12, 'B_R_Calf', .8, (.3, 1, 0)), 'feet': ('Walking', 6, 'B_L_Foot', .5, (-.5, -.8, .1)),
         'death': ('Death', 30, 'B_Spine', 1.6, (.6, -.6, .6)), 'attack': ('Cast', 12, 'B_Spine1', 1.2, (-.7, -.7, .2)),
         'rcuff': ('Standing', 0, 'B_R_Forearm', .25, (-.6, -.8, .1)), 'lcuff': ('Standing', 0, 'B_L_Forearm', .25, (.6, -.8, .1)),
         'death8': ('Death', 8, 'B_Pelvis', 1.4, (.6, -.8, .3)), 'death16': ('Death', 16, 'B_Pelvis', 1.4, (.6, -.8, .4)),
         'dead': ('Death', 48, 'B_Pelvis', 1.6, (.4, -.6, .8)), 'walk': ('Walking', 6, 'B_Pelvis', 1.2, (.3, -1, 0)),
         'walk_back': ('Walking', 12, 'B_Pelvis', 1.2, (-.3, 1, 0)), 'cast': ('Cast', 16, 'B_Spine1', 1.2, (.3, -1, .2)),
         'bodice': ('Standing', 0, 'B_Spine1', .45, (0, -1, .1)), 'hair_back': ('Standing', 0, 'B_Spine2', .8, (0, 1, .1)),
         'cape_side': ('Standing', 0, 'B_Pelvis', 1.3, (1, .3, 0)),
         'cast20_rside': ('Cast', 20, 'B_R_Calf', .5, (-.3, -1, 0)), 'cast20_back': ('Cast', 20, 'B_Pelvis', 1.0, (0, 1, -.1)),
         'skirt_std': ('Standing', 24, 'B_Pelvis', 1.0, (0, -1, -.1)), 'skirt_walk12': ('Walking', 12, 'B_Pelvis', 1.0, (0, -1, -.1)),
         'skirt_walk6': ('Walking', 6, 'B_Pelvis', 1.0, (.4, -1, -.1)), 'skirt_cast20': ('Cast', 20, 'B_Pelvis', 1.0, (.4, -1, -.1)),
         'shoulder_l': ('Standing', 0, 'B_L_Clavicle', .34, (.6, -.8, .4)), 'shoulder_r': ('Standing', 0, 'B_R_Clavicle', .34, (-.6, -.8, .4))}
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
