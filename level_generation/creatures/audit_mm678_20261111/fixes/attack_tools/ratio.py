#!/usr/bin/env python3
"""Motion ratio of clips against the audit's MM9 reference (score.py's definition: mean of p90 reach, moving share
and peak speed over the MM9 median of the body type), plus the clip's deformation shares beyond Standing.

    ratio.py <glb> <clip>[,<clip>...] [--body biped|other]
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'claude_shared'))
import motion_audit  # noqa: E402

REF = json.loads((HERE.parents[1] / 'scores.json').read_text())['mm9_attack_reference']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('glb')
    ap.add_argument('clips')
    ap.add_argument('--body', default='biped')
    args = ap.parse_args()
    a = motion_audit.Audit(args.glb)
    r = REF[args.body]
    st, _ = a.clip('Standing', 30)
    for clip in args.clips.split(','):
        m, _ = a.clip(clip, 30)
        ratio = (m['amp_p90'] / r['amp_p90'] + m['body_share'] / r['body_share'] + m['peak_speed'] / r['peak_speed']) / 3
        beyond = {k: round(v['bad_pct'] - st['deform'].get(k, {}).get('bad_pct', 0), 1) for k, v in m['deform'].items()}
        print(f"{clip}: ratio {ratio:.2f}  reach {m['amp_p90']:.3f}  share {m['body_share']:.3f}  peak {m['peak_speed']:.2f}"
              f"  torso {m['torso_turn_deg']}  len {m['length_s']}  hand_inside {m['hand_inside_pct']}%"
              f"  deform beyond Standing {beyond}")


if __name__ == '__main__':
    main()
