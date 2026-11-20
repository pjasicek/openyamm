"""Crest clearance gate: every crystal is rigid on one bone while the hide under it blends between bones, so a bending
back could open a gap under a root or swallow it. Per clip and frame (all of them), the root and axis follow the
crystal's bone; a ray down the axis from 25 cm above finds the deformed hide. offset = hide height above the root
along the axis (+ swallowed, - gap). The prism reaches 1.3 r under the root, so a gap deeper than
that would show the crystal's open bottom. Also the nearest tip-to-tip distance between crystals on different bones
(collisions as the back bends). Writes review/crest_clearance.json. Args: -- <blend>"""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]
for o in bpy.data.objects:
    if o.name.startswith('Crest'):
        o.hide_viewport = True
layout = json.load(open(C.path('work/crest_layout.json')))
REST = {b.name: b.matrix_local.copy() for b in rig.data.bones}
SIZES = {'short': (0.42, 0.85), 'full': (1.0, 1.0), 'tall': (1.3, 1.05)}
out = {}
for clip in ['Standing', 'Walking', 'Running', 'Attack', 'Bite', 'Hit', 'Death', 'Dead', 'Fidget']:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    worst_gap, worst_sw, min_tip = 0.0, 0.0, 9.0
    worst = {True: None, False: None}
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        bvh = BVHTree.FromObject(body, dg)
        tips = []
        for c in layout:
            M = rig.matrix_world @ rig.pose.bones[c['bone']].matrix @ REST[c['bone']].inverted()
            p = M @ Vector(c['p']); a = (M.to_3x3() @ Vector(c['axis'])).normalized()
            hit = bvh.ray_cast(p + a * 0.25, -a, 0.6)
            off = 0.25 - hit[3] if hit[0] is not None else -0.3
            off_rel = off / (1.3 * c['radius'])          # in units of the full crest's sink (1.3 r)
            if off_rel < worst_gap or off_rel > worst_sw:
                culprit = (round(off_rel, 2), c['bone'], c['row'], round(c['p'][1], 2), f)
                worst[off_rel < 0] = culprit
            worst_gap = min(worst_gap, off_rel); worst_sw = max(worst_sw, off_rel)
            tips.append((c['bone'], p, a, c['h']))
        for size, (hs, rs) in SIZES.items():          # tips of every crest set (the tall one leans furthest)
            for i in range(len(tips)):
                for j in range(i + 1, len(tips)):
                    if tips[i][0] != tips[j][0]:
                        ti = tips[i][1] + tips[i][2] * tips[i][3] * hs; tj = tips[j][1] + tips[j][2] * tips[j][3] * hs
                        min_tip = min(min_tip, (ti - tj).length)
    out[clip] = {'gap_in_sinks': round(worst_gap, 3), 'gap_in_short_sinks': round(worst_gap / 0.9, 3),
                 'swallow_in_sinks': round(worst_sw, 3),
                 'min_tip_distance_m_across_bones_all_sets': round(min_tip, 3)}
    print('CREST_CLEAR', clip, out[clip], 'gap at', worst[True], 'swallow at', worst[False])
json.dump(out, open(C.path('review/crest_clearance.json'), 'w'), indent=1)
