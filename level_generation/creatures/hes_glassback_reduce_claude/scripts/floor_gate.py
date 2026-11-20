#!/usr/bin/env python3
"""Floor and stride gate on the runtime GLB without Blender (claude_shared/floor/glb_pose.py, the floor audit's own
evaluator): per clip the lowest point at every key in world units for each tier scale (tolerance: the larger of 2.5
units and 1 % of the standing height); walking/running never with every foot off; the corpse on the floor. Strides:
the planted feet's backward travel per loop. Writes review/floor_gate.json (or the name given). Args: glb [out name]"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared/floor'))
import glb_pose
SCALES = {'hes_glassback_pup': 100.0, 'hes_glassback': 125.0, 'hes_glassback_bull': 143.75}
m = glb_pose.Model(glb_pose.Glb(Path(sys.argv[1])))
res = {}
stand_h = m.highest('Standing', 0.0)
for clip in m.clips:
    times = m.clip_times(clip)
    lows = [m.lowest(clip, t) for t in times]
    res[clip] = {'lowest_m': round(min(lows), 4), 'highest_low_m': round(max(lows), 4), 'keys': len(times)}
print('STAND height m', round(stand_h, 3))
tol = {d: max(2.5, 0.01 * stand_h * s) for d, s in SCALES.items()}
ok = True
for clip, r in res.items():
    for d, s in SCALES.items():
        lo, hi = r['lowest_m'] * s, r['highest_low_m'] * s
        bad = lo < -tol[d] or (clip in ('Standing', 'Walking', 'Running', 'Dead', 'Fidget', 'Hit') and hi > tol[d]) \
            or (clip == 'Dead' and abs(lo) > tol[d])
        if clip == 'Running' and hi > tol[d] and lo >= -tol[d]:
            bad = False                     # a run may leave the floor
        ok &= not bad
        r.setdefault('world', {})[d] = [round(lo, 2), round(hi, 2), 'FAIL' if bad else 'ok']
    print('FLOOR', clip, r)
# strides: joint world positions of the Foot_* joints; planted = lowest 45 % of the loop per foot
names = [m.glb.json['nodes'][j]['name'] for j in m.glb.json['skins'][0]['joints']]
for clip in ('Walking', 'Running'):
    times = m.clip_times(clip); T = times[-1]
    per = []
    for leg in ('FL', 'FR', 'ML', 'MR', 'HL', 'HR'):
        j = m.glb.json['skins'][0]['joints'][names.index(f'Foot_{leg}')]
        pts = np.array([m.world(m.sample(clip, t))[j][:3, 3] for t in times])
        low = pts[:, 1] <= np.percentile(pts[:, 1], 45)
        dz = np.diff(pts[:, 2]); dt = np.diff(times)
        sel = low[1:] & low[:-1]
        per.append(float(np.median(dz[sel] / dt[sel])) * T)     # glTF +Z = Blender -Y (backward)
    res[clip]['stride_m'] = round(float(np.median(per)), 4)
    print('STRIDE', clip, res[clip]['stride_m'], [round(x, 3) for x in per])
res['tolerance_units'] = tol; res['pass'] = bool(ok); res['standing_height_m'] = round(stand_h, 4)
json.dump(res, open(ROOT / 'review' / (sys.argv[2] if len(sys.argv) > 2 else 'floor_gate.json'), 'w'), indent=1)
print('GATE', 'pass' if ok else 'FAIL')
