#!/usr/bin/env python3
"""Head and neck posture per clip (follow-up 3, 2026-11-12: "isnt her head like crouched too forward?").
glTF y up, +z forward (toes ahead of the feet). Per clip, sampled at 30 fps, mean (min..max):
  chest_head  angle of the upper chest -> head joint line from vertical, deg (+ = head ahead of the chest)
  neck        angle of the neck -> head joint line from vertical, deg (+ = forward)
  head_fwd    head joint ahead of the upper chest, cm;  head_sh: head joint ahead of the shoulders (upper-arm joints), cm
  trunk       pelvis -> upper chest line from vertical, deg (+ = leaning forward)
  pitch       head's facing pitch relative to its rest facing, deg (+ = chin down)
  arm_back    the most backward upper-arm swing (shoulder -> elbow from straight down in the sagittal plane, deg, - = behind), L/R
Usage: head_posture.py <glb> <profile: mm9|mixamo> [Clip[:t0-t1] ...] [--json out]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

PROFILES = {
    'mm9': dict(pelvis='FHP Pelvis', chest='FHP Spine3', neck='FHP Neck', head='FHP Head',
                arms=(('FHP L UpperArm', 'FHP L Forearm'), ('FHP R UpperArm', 'FHP R Forearm'))),
    'mixamo': dict(pelvis='mixamorig:Hips', chest='mixamorig:Spine2', neck='mixamorig:Neck', head='mixamorig:Head',
                   arms=(('mixamorig:LeftArm', 'mixamorig:LeftForeArm'), ('mixamorig:RightArm', 'mixamorig:RightForeArm'))),
}


def ang(v):
    return np.degrees(np.arctan2(v[..., 2], v[..., 1]))


def measure(path, profile, specs):
    m = Model(Glb(path)); names = [n.get('name') for n in m.glb.json['nodes']]; ix = {n: i for i, n in enumerate(names)}
    P = PROFILES[profile]
    rest = m.world({})
    Rh0 = rest[ix[P['head']]][:3, :3]
    fwd0 = np.array([0, 0, 1.0])
    out = {}
    for spec in specs:
        clip, _, rng = spec.partition(':')
        ts = m.clip_times(clip)
        t0, t1 = (float(x) for x in rng.split('-')) if rng else (ts[0], ts[-1])
        T = np.arange(t0, t1 + 1e-6, 1 / 30)
        rows = []
        for t in T:
            W = m.world(m.sample(clip, float(t)))
            p = lambda n: W[ix[n]][:3, 3]
            ch, nk, hd, pv = p(P['chest']), p(P['neck']), p(P['head']), p(P['pelvis'])
            sh = (p(P['arms'][0][0]) + p(P['arms'][1][0])) / 2
            Rh = W[ix[P['head']]][:3, :3]
            f = Rh @ Rh0.T @ fwd0
            arms = []
            for u, fa in P['arms']:
                v = p(fa) - p(u)
                arms.append(np.degrees(np.arctan2(v[2], -v[1])))
            rows.append([ang(hd - ch), ang(hd - nk), (hd[2] - ch[2]) * 100, (hd[2] - sh[2]) * 100, ang(ch - pv),
                         np.degrees(np.arcsin(np.clip(-f[1], -1, 1))), arms[0], arms[1]])
        a = np.array(rows)
        keys = ['chest_head', 'neck', 'head_fwd', 'head_sh', 'trunk', 'pitch', 'armL', 'armR']
        out[spec] = {k: [round(float(a[:, i].mean()), 1), round(float(a[:, i].min()), 1), round(float(a[:, i].max()), 1)]
                     for i, k in enumerate(keys)}
    return out


if __name__ == '__main__':
    args = sys.argv[1:]; js = None
    if '--json' in args:
        i = args.index('--json'); js = args[i + 1]; del args[i:i + 2]
    res = measure(args[0], args[1], args[2:])
    print(f'{"clip":18s} {"chest_head":>18s} {"neck":>18s} {"head_fwd cm":>18s} {"head_sh cm":>18s} {"trunk":>18s} {"pitch":>18s} {"armL":>18s} {"armR":>18s}')
    for c, d in res.items():
        print(f'{c:18s} ' + ' '.join(f'{v[0]:6.1f} ({v[1]:5.1f}..{v[2]:5.1f})'.rjust(18) for v in d.values()))
    if js:
        Path(js).write_text(json.dumps(res, indent=1))
