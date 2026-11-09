"""Close-ups of the source and ladder candidates in work/<blend> (default ladder.blend): head, six hands, torso, back,
tail, Attack and Death poses; textured (Eevee) and
(workbench + cavity). Writes review/close/<label>_<spot>_<mode>.png and review/close/sheet_<blend stem>.png.
Usage: blender -b -P close_ladder.py -- <blend> <Cand_55,...> [spot,...]"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
blend, cands = args[0], args[1].split(',')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
objs = {'source': bpy.data.objects['Body'], **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in cands if c}}
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
if 'CloseSun' not in bpy.data.objects:
    import math
    sun = bpy.data.objects.new('CloseSun', bpy.data.lights.new('CloseSun', 'SUN')); sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
    world = bpy.data.worlds.new('CloseW'); sc.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sc.view_settings.view_transform = 'Standard'
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
# (action, frame, bone, ortho size, view direction); the Naga faces -Y
SPOTS = {'head_front': ('Standing', 0, 'Head', .32, (0, -1, .1)), 'head_q34': ('Standing', 0, 'Head', .32, (.7, -.7, .2)),
         'head_side': ('Standing', 0, 'Head', .32, (-1, 0, .1)), 'head_back': ('Standing', 0, 'Head', .4, (0, 1, .2)),
         'hands_l': ('Standing', 0, 'L2_Forearm', .9, (.8, -.6, .1)), 'hands_r': ('Standing', 0, 'R2_Forearm', .9, (-.8, -.6, .1)),
         'hand_l1': ('Standing', 0, 'L1_Hand', .2, (.5, -.8, .2)), 'hand_r3': ('Standing', 0, 'R3_Hand', .2, (-.5, -.8, .2)),
         'torso': ('Standing', 0, 'Chest', .7, (0, -1, .05)), 'back': ('Standing', 0, 'Chest', .8, (0, 1, .1)),
         'tail': ('Standing', 0, 'Serpent_08', 2.2, (1, -.2, .6)), 'tail_tip': ('Standing', 0, 'Serpent_17', .8, (-.6, -.3, .7)),
         'coil': ('Standing', 0, 'Serpent_09', .6, (.6, -.2, .8)), 'coil_side': ('Standing', 0, 'Serpent_10', .6, (1, .3, .2)),
         'attack': ('Attack', 24, 'Chest', 1.6, (.3, -1, .2)), 'death': ('Death', 36, 'Chest', 2.2, (1, -.3, .5))}
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
