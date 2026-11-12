#!/usr/bin/env python3
"""Motion ratio, deformation beyond Standing and floor of one clip (attacks-2 stream, 2026-11-11).

    attack_ratio.py <glb> [--clip Attack] [--body other|biped]

The ratio is score.py's: the mean of p90 reach, moving share and peak speed over the MM9 medians of the body type
(read from the audit's table.json). Deformation: per region, the clip's worst bad share minus Standing's (the brief's
"beyond Standing"). Floor: the lowest visible LOD0 point over the clip (glb_pose, metres; 0 is the floor).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'claude_shared'))
import motion_audit  # noqa: E402

TABLE = HERE.parents[1] / 'table.json'


def reference(body):
    models = json.loads(TABLE.read_text())['models']
    rows = [r for r in models.values() if r['mm9'] and r['body'] == body and r['model'] not in
            ('mm9_icky', 'mm9_lobberpod') and 'attack_melee' in r['combat']
            and r['combat']['attack_melee']['clip'].lower() not in ('standing', 'fidget', 'walking')]
    return {k: sorted(r['combat']['attack_melee'][k] for r in rows)[len(rows) // 2]
            for k in ('amp_p90', 'body_share', 'peak_speed')}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('glb')
    p.add_argument('--clip', default='Attack')
    p.add_argument('--body', default='other')
    a = p.parse_args()
    ref = reference(a.body)
    au = motion_audit.Audit(a.glb)
    res, frames = au.clip(a.clip, 30)
    stand, _ = au.clip('Standing', 30)
    ratio = (res['amp_p90'] / ref['amp_p90'] + res['body_share'] / ref['body_share']
             + res['peak_speed'] / ref['peak_speed']) / 3
    beyond = {r: round(v['bad_pct'] - stand['deform'].get(r, {}).get('bad_pct', 0), 1) for r, v in res['deform'].items()}
    low = frames[:, :, 1].min(axis=1)
    print(f"{Path(a.glb).name} {a.clip}: ratio {ratio:.2f}  reach {res['amp_p90']:.3f}  share {res['body_share']:.3f}  "
          f"speed {res['peak_speed']:.2f}  turn {res['torso_turn_deg']}  len {res['length_s']}  H {au.height:.3f}")
    print(f"  beyond Standing: {beyond}  hotspot {res['hotspot']}")
    print(f"  floor: lowest {low.min():.4f} m at {np.argmin(low) / 30:.2f} s (first frame {low[0]:.4f})  "
          f"hand inside {res['hand_inside_pct']} %  accel p99 {res['accel_p99']}")
    print(f"  region reach {res['region_amp']}")
    # The same three numbers over the surface that is visible in the clip's first frame: parts hidden by a zero scale
    # (a Juggernaut's death fragments, 48 % of its rest area) never move and cap the audit's share.
    _, scale, _, _ = au.pose(a.clip, au.model.clip_times(a.clip)[0])
    vis = scale >= 0.2
    if vis.sum() < len(vis):
        w = au.vertex_area * vis
        w = w / w.sum()
        disp = np.linalg.norm(frames - frames[0], axis=2).max(axis=0) / au.height
        dt = res['length_s'] / (len(frames) - 1)
        speed = np.linalg.norm(np.diff(frames, axis=0), axis=2) / au.height / dt
        amp = motion_audit.weighted_quantile(disp, w, 0.9)
        share = float(w[disp > 0.05].sum())
        peak = max(float(motion_audit.weighted_quantile(row, w, 0.95)) for row in speed)
        vr = (amp / ref['amp_p90'] + share / ref['body_share'] + peak / ref['peak_speed']) / 3
        print(f"  visible surface only ({100 * (1 - vis.mean()):.0f} % of vertices hidden): ratio {vr:.2f}  "
              f"reach {amp:.3f}  share {share:.3f}  speed {peak:.2f}")


if __name__ == '__main__':
    main()
