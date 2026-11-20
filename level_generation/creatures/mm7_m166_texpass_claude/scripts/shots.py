#!/usr/bin/env python3
"""Identical-camera review-viewer shots of every tier, installed (before) and texture pass (tp), and the sheet per
target world: claude_shared/texpass_viewer_shots.py with texpass.json "shots" (name:clip:time:view:focus[:cam:target]).
Writes review/shots/{before,tp}/<tier>_<name>.png and review/texpass_sheet_<tierprefix>.png."""
import subprocess
import sys

import tp

TOOL = tp.CREATURES / 'claude_shared' / 'texpass_viewer_shots.py'


def auto_specs():
    """Free cameras from the posed model (texpass.json auto_shots: clip, time, head_bone [, head_dist 0.45]): head front
    and 3/4, top 3/4, side, whole-body 3/4, aimed from the body centre towards the head bone (the facing)."""
    import numpy as np
    sys.path.insert(0, str(tp.CREATURES / 'claude_shared'))
    import motion_audit as MA
    a = tp.CFG['auto_shots']
    audit = MA.Audit(tp.installed())
    P, _, _, world = audit.pose(a['clip'], a.get('time', 0))
    joint = next(j for j in audit.model.joints if audit.glb.json['nodes'][j].get('name') == a['head_bone'])
    head = world[joint][:3, 3]
    lo, hi = P.min(0), P.max(0)
    centre, ext = (lo + hi) / 2, float((hi - lo).max())
    up = np.array([0, 1.0, 0])
    fwd = head - centre
    fwd[1] = 0
    fwd = fwd / max(np.linalg.norm(fwd), 1e-9) if np.linalg.norm(fwd) > 1e-6 else np.array([0, 0, 1.0])
    side = np.cross(up, fwd)
    unit = lambda v: v / np.linalg.norm(v)
    hd = a.get('head_dist', 0.45) * ext
    clip, t = a['clip'], a.get('time', 0)
    fmt = lambda v: ','.join(f'{x:.4f}' for x in v)
    shots = [('hf', head, head + unit(fwd + 0.15 * up) * hd),
             ('hq', head, head + unit(fwd + side + 0.3 * up) * hd),
             ('top', centre, centre + unit(0.5 * fwd + 1.2 * up - 0.6 * side) * 1.5 * ext),
             ('side', centre, centre + unit(-side + 0.15 * up) * 1.5 * ext),
             ('bq', centre, centre + unit(fwd + 0.8 * side + 0.35 * up) * 2.0 * ext)]
    return [f'{n}:{clip}:{t}:front:body:{fmt(cam)}:{fmt(tgt)}' for n, tgt, cam in shots]


specs = auto_specs() if 'auto_shots' in tp.CFG else tp.CFG['shots']
print('SPECS', specs)
names = ','.join(s.split(':')[0] for s in specs)
tiers = list(tp.CFG['tiers'])
for tag in ('before', 'tp'):
    out = tp.HERE / 'review' / 'shots' / tag
    out.mkdir(parents=True, exist_ok=True)
    for tier in tiers:
        subprocess.run([sys.executable, str(TOOL), 'shots', str(tp.HERE), str(out), f'{tier}_{tag}', *specs], check=True)
        for s in specs:            # <tier>_<tag>_<name>.png -> <tier>_<name>.png
            name = s.split(':')[0]
            (out / f'{tier}_{tag}_{name}.png').replace(out / f'{tier}_{name}.png')
groups = {}
for tier in tiers:
    groups.setdefault(tier.rsplit('_', 1)[0], []).append(tier)
for prefix, group in groups.items():
    subprocess.run([sys.executable, str(TOOL), 'sheet', str(tp.HERE / 'review' / f'texpass_sheet_{prefix}.png'),
                    str(tp.HERE / 'review' / 'shots' / 'before'), str(tp.HERE / 'review' / 'shots' / 'tp'),
                    ','.join(group), names], check=True)
