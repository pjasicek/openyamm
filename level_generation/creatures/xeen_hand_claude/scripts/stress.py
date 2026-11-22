"""Stress views of the rig: weights (dominant bone colours), rest with bones, fist, spread, claw + open lids.
review/stress_*.png. Args: -- [blend in work/ (rig_v1.blend)]"""
import bpy, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, handpose as H
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0] if a else 'rig_v1.blend'))
rig = bpy.data.objects['Hand_Rig']; ob = bpy.data.objects['Hand']; me = ob.data
# dominant-bone colours as materials
rng = np.random.default_rng(3)
gn = [g.name for g in ob.vertex_groups]
mats = []
for i, g in enumerate(gn):
    m = bpy.data.materials.new(g); m.diffuse_color = (*rng.uniform(0.2, 1.0, 3), 1); me.materials.append(m)
dom = np.zeros(len(me.vertices), int)
for v in me.vertices:
    if v.groups: dom[v.index] = max(v.groups, key=lambda e: e.weight).group
for p in me.polygons:
    p.material_index = int(np.bincount(dom[list(p.vertices)]).argmax())
VIEWS = {'front': ((0, -3, 0.25), (0, 0, 0.25)), 'side': ((-3, 0, 0.25), (0, 0, 0.25)),
         'quarter': ((1.6, -2.2, 1.4), (0, 0, 0.22))}
POSES = {
    'weights': None,
    'fist': dict(flex={'Thumb': (35, 35, 40), 'Index': (70, 85, 60), 'Middle': (70, 85, 60), 'Ring': (70, 85, 60),
                       'Pinky': (70, 85, 60)}),
    'spread': dict(flex={'Thumb': (-15, -15, -10), 'Index': (-30, -30, -20), 'Middle': (-30, -30, -20),
                         'Ring': (-30, -30, -20), 'Pinky': (-30, -30, -20)}, spread=14, lips=55),
}
for pname, ps in POSES.items():
    H.reset(rig)
    if ps: H.hand(rig, **ps)
    C.COLOR_OVERRIDE = 'MATERIAL' if pname == 'weights' else None
    for vn, (loc, tgt) in VIEWS.items():
        C.render(loc, tgt, 0.75, os.path.join(HERE, 'review', f'stress_{pname}_{vn}.png'), res=(500, 420), floor=False,
                 bones=(pname == 'weights'))
