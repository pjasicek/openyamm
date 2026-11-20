"""Close-ups of the source and ladder candidates (work/<blend>) for the MM7 Hydra (faces -y; heads 1..5 from the
hydra's right (-x) to its left (+x)): per head front, outer side, three-quarter and the mouth from below; the five
head-to-neck loft joints from behind; body spots (back, flank, paws, tail, belly) and Attack, Death, Running.
Textured (Eevee) and clay (workbench + cavity). The welded source's custom normals are rotated by the weld, so they
are cleared here (judge final shading from GLBs, glb_close.py).
Usage: blender -b -P close_hydra.py -- <blend> <Cand_60,...|-> [spot,...]  -> review/close/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
cands = [] if args[1] == '-' else args[1].split(',')
objs = {'source': src, **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in cands}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 10
if not any(o.type == 'LIGHT' for o in sc.objects):
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
    sun.rotation_euler = (0.8, 0, -0.6); sc.collection.objects.link(sun)
if sc.world is None:
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('CLOSE_RES', '420'))
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
pb = rig.pose.bones
bone = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
LAST = {1: 'Neck1_10', 2: 'Neck2_07', 3: 'Neck3_07', 4: 'Neck4_07', 5: 'Neck5_07'}
SPOTS = {}
for k in range(1, 6):
    sx = -1 if k <= 3 else 1
    SPOTS[f'h{k}_front'] = ('Standing', 0, f'Head{k}', .6, (0, -1, .15))
    SPOTS[f'h{k}_side'] = ('Standing', 0, f'Head{k}', .6, (sx, 0, .1))
    SPOTS[f'h{k}_q34'] = ('Standing', 0, f'Head{k}', .6, (sx * .7, -.7, .3))
    SPOTS[f'h{k}_mouth'] = ('Standing', 0, f'Head{k}', .4, (sx * .3, -1, -.45))
    SPOTS[f'h{k}_loft'] = ('Standing', 0, LAST[k], .6, (sx * .6, .6, .5))
SPOTS.update({'heads_front': ('Standing', 0, 'Head3', 2.0, (0, -1, .2)), 'heads_top': ('Standing', 0, 'Head3', 2.0, (0, -.3, 1)),
              'back': ('Standing', 0, 'Spine2', 1.6, (.4, .3, 1)), 'flank_r': ('Standing', 0, 'Spine2', 1.8, (-1, 0, .1)),
              'flank_l': ('Standing', 0, 'Spine2', 1.8, (1, 0, .1)), 'belly': ('Standing', 0, 'Spine2', 1.6, (.3, 0, -1)),
              'fpaw_r': ('Standing', 0, 'FrontPaw_R', .4, (-.5, -.8, .3)), 'hpaw_l': ('Standing', 0, 'HindPaw_L', .4, (.7, -.5, .3)),
              'tail': ('Standing', 0, 'Tail5', 1.4, (1, .2, .5)), 'necks_back': ('Standing', 0, 'Spine3', 1.6, (0, 1, .5)),
              'attack': ('Attack', 13, 'Head3', 2.0, (-.7, -.7, .2)), 'death': ('Death', 30, 'Spine2', 3.0, (.6, -.6, .6)),
              'run': ('Running', 6, 'Spine2', 3.0, (-1, -.3, .2))})
# extra spots in the rest pose at rest-space points: CLOSE_SPOTS='name@x,y,z@size@dx,dy,dz;...' (drift/sliver clusters)
POINTS = {}
for item in filter(None, os.environ.get('CLOSE_SPOTS', '').split(';')):
    name, p, size, d = item.split('@')
    POINTS[name] = tuple(float(x) for x in p.split(',')); SPOTS[name] = ('REST', 0, None, float(size), tuple(float(x) for x in d.split(',')))
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
for spot, (act, frame, b, size, d) in SPOTS.items():
    if act == 'REST':
        rig.animation_data.action = None
        for p in pb:
            p.matrix_basis.identity()
        sc.frame_set(0); c = Vector(POINTS[spot])
    else:
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame); c = bone(b)
    cam.location = c + Vector(d).normalized() * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    # head spots: a slab of +-0.35 m around the head, so the neighbouring heads do not hide it
    cam.data.clip_start, cam.data.clip_end = ((4 - .35, 4 + .35) if spot.startswith('h') and spot[1].isdigit()
                                              and not spot.endswith('loft') else (.1, 10))
    for label, o in objs.items():
        for p in objs.values():
            p.hide_render = p is not o
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            if os.environ.get('CLOSE_MODES') and mode not in os.environ['CLOSE_MODES'].split(','):
                continue
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE', list(objs), list(SPOTS))
