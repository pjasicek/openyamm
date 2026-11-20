"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Treant (faces -y, 4.0 m): face front and
three-quarter (Standing: mouth closed, eyes sunk), the open mouth and eyes at the Attack wake and the Hit gape, the crown
from above and three-quarter, every crown sector, the spire, the root skirt front/back/sides, the trunk back, the Attack
impact lash and Death; textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are rotated
by the weld, so they are cleared here (judge final shading from GLBs, glb_close.py).
Extra spots: CLOSE_POINTS="name:clip:frame:x,y,z:size;..." (rest-pose point, posed by the nearest source vertex).
Usage: blender -b -P close_treant.py -- <blend> <Cand_75,...> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
objs = {'source': src, **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in args[1].split(',') if c}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
if not any(o.type == 'LIGHT' for o in sc.objects):
    import math
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 20
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '420'))
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
# (clip, frame (24 fps scene frames), bone or rest point, ortho size, view direction)
SPOTS = {'face_front': ('Standing', 0, 'Trunk1', 1.6, (0, -1, .1)), 'face_q34': ('Standing', 0, 'Trunk1', 1.7, (-.7, -.7, .15)),
         'mouth_open': ('Attack', 14, 'Jaw', 1.1, (0, -1, .15)), 'mouth_open_q34': ('Hit', 4, 'Jaw', 1.2, (.7, -.7, .1)),
         'eyes_open': ('Attack', 14, 'Trunk2', .9, (0, -1, .05)),
         'crown_top': ('Standing', 0, 'Trunk3', 3.9, (.05, -.1, 1)), 'crown_q34': ('Standing', 0, 'Trunk3', 3.4, (.7, -.7, .4)),
         'crown_back': ('Standing', 0, 'Trunk3', 3.4, (-.3, 1, .3)),
         'crown_l': ('Standing', 0, 'Trunk3', 3.4, (1, 0, .2)), 'crown_r': ('Standing', 0, 'Trunk3', 3.4, (-1, 0, .2)),
         'spire': ('Standing', 0, 'Spire', 1.6, (.6, -.8, .2)),
         'roots_front': ('Standing', 0, 'Root', 3.2, (0, -1, .45)), 'roots_back': ('Standing', 0, 'Root', 3.2, (0, 1, .45)),
         'roots_l': ('Standing', 0, 'Root', 3.2, (1, 0, .45)), 'roots_r': ('Standing', 0, 'Root', 3.2, (-1, 0, .45)),
         'roots_top': ('Standing', 0, 'Root', 3.6, (0, -.15, 1)),
         'trunk_back': ('Standing', 0, 'Trunk2', 2.2, (0, 1, .1)),
         'attack': ('Attack', 16, 'Trunk2', 4.6, (-.6, -.8, .2)), 'death': ('Death', 14, 'Trunk1', 4.2, (.6, -.8, .3)),
         'dead': ('Dead', 10, 'Trunk1', 3.0, (.6, -.8, .3))}
import numpy as np
for spec in filter(None, os.environ.get('CLOSE_POINTS', '').split(';')):
    nm, clip, fr, p, sz = spec.split(':')
    SPOTS[nm] = (clip, int(fr), Vector([float(x) for x in p.split(',')]), float(sz), (.5, -.8, .3))
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
rest = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
for spot, (act, frame, b, size, d) in SPOTS.items():
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    if isinstance(b, str):
        c = bone(b)
    else:
        i = int(np.argmin(np.linalg.norm(rest - np.array(b), axis=1)))
        ev = src.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        c = ev.matrix_world @ m.vertices[i].co; ev.to_mesh_clear()
    cam.location = c + Vector(d).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    # point spots: clip everything in front of the spot so it is not hidden by other strands
    cam.data.clip_start = 6 - size if not isinstance(b, str) else 0.1
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
