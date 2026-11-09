"""Orthographic review renders of the Treant (Workbench). Character faces -Y.
Args: <blend> <out_dir> [action[:t1,t2,...] ...]  env: VIEWS=front,q34,side,back,top  TEX=1 (texture colours)
      SIZE=384  OS=<ortho scale>  CZ=<camera centre z>
Without actions renders the rest pose as rest_<view>.png; with actions <action>_<k>_<view>.png at clip times (s)."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
blend, out = a[0], a[1]; acts = a[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene
common.workbench_clay(scene, textured=os.environ.get('TEX') == '1')
if os.environ.get('PIECES'):                 # colour pieces: PIECES=all or comma list (others grey)
    import numpy as np, colorsys
    ob = bpy.data.objects['Body']; me = ob.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    sel = None if os.environ['PIECES'] == 'all' else {int(x) for x in os.environ['PIECES'].split(',')}
    col = np.full((len(pv), 4), 0.6); col[:, 3] = 1
    for p in np.unique(pv):
        if sel is None or p in sel:
            col[pv == p, :3] = colorsys.hsv_to_rgb((p * 0.618) % 1, 0.8, 0.95)
    at = me.color_attributes.new('pc', 'FLOAT_COLOR', 'POINT'); at.data.foreach_set('color', col.ravel())
    me.color_attributes.active_color = at
    scene.display.shading.color_type = 'VERTEX'
if os.environ.get('TEX') != '1':
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
scene.display.shading.show_backface_culling = os.environ.get('CULL') == '1'
scene.display.shading.show_specular_highlight = False
size = int(os.environ.get('SIZE', '384'))
scene.render.resolution_x = scene.render.resolution_y = size
OS = float(os.environ.get('OS', '4.6')); CZ = float(os.environ.get('CZ', '2.0'))
VIEWS = os.environ.get('VIEWS', 'front,q34,side,back').split(',')
ANG = {'front': 0, 'q34': 35, 'side': 90, 'back': 180, 'rside': -90, 'rq34': -35}
cams = {}
for v in VIEWS:
    if v == 'top':
        cams[v] = common.ortho_camera('cam_top', (0, 0, 12), (0, 0, 0), OS)
        continue
    ang = math.radians(ANG[v]); d = 12
    cams[v] = common.ortho_camera('cam_' + v, (math.sin(ang) * d, -math.cos(ang) * d, CZ), (math.radians(90), 0, ang), OS)
rig = bpy.data.objects.get('Rig')


def shoot(tag):
    for v, cam in cams.items():
        scene.camera = cam; scene.render.filepath = os.path.join(out, f'{tag}_{v}.png')
        bpy.ops.render.render(write_still=True)


if not acts:
    shoot('rest')
for spec in acts:
    name, _, ts = spec.partition(':')
    A = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = A
    if len(A.slots):
        rig.animation_data.action_slot = A.slots[0]
    fps = scene.render.fps / scene.render.fps_base
    f0, f1 = A.frame_range
    times = [float(t) for t in ts.split(',')] if ts else [k * (f1 - f0) / fps / 4 for k in range(5)]
    for k, t in enumerate(times):
        f = f0 + t * fps
        scene.frame_set(int(f), subframe=f - int(f))
        shoot(f'{name}_{k}')
    print('SHOTS', name, times)
print('SHOTS done', out)
