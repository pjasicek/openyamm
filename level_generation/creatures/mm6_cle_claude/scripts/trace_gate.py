#!/usr/bin/env python3
"""Gate over work/trace_<clip>.json (trace_clip.py, 48 fps as the viewer plays); adapted from
mm6_thf_claude/scripts/trace_gate.py. Per clip and side the worst hand-ring drift in the forearm frame, wrist swing /
twist, forearm twist and hand turn per half-frame; the staff turn per half-frame; the widest cloak tear (warning). When
work/<clip>_intent.json exists (author_clips.py), each key's played staff grip and ring centre are compared with the
intent. Args: clip ... Exit 1 when a limit is exceeded."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent.parent
LIMITS = {'ring_drift_mm': 8.0, 'wrist_swing': 60.0, 'wrist_twist': 45.0, 'forearm_twist': 90.0, 'hand_turn_deg': 45.0}
STAFF_TURN = 30.0
INTENT_CM = 4.0
CLOAK_CM = 3.0
bad = False
for clip in sys.argv[1:]:
    T = json.load(open(HERE / 'work' / f'trace_{clip}.json'))
    parts = []
    for k in 'RL':
        for m, lim in LIMITS.items():
            v = max(((min(r[k][m], 360 - r[k][m]) if m == 'hand_turn_deg' else abs(r[k][m])), r['step'])
                    for r in T['rows'])
            if v[0] > lim:
                parts.append(f'{k} {m} {v[0]:.1f} > {lim} at half-frame {v[1]}')
    st = max((r['staff_turn_deg'], r['step']) for r in T['rows'])
    if st[0] > STAFF_TURN:
        parts.append(f'staff turn {st[0]:.1f} > {STAFF_TURN} deg at half-frame {st[1]}')
    intent = HERE / 'work' / f'{clip}_intent.json'
    if intent.exists():
        rows = {r['step']: r for r in T['rows']}
        for key in json.load(open(intent)):
            r = rows.get(int(round(key['f'] * T['fps'] / 24)))
            if r is None:
                continue
            dg = float(np.linalg.norm(np.array(r['staff']['grip']) - np.array(key['grip']))) * 100
            dh = float(np.linalg.norm(np.array(r['staff']['head']) - np.array(key['head']))) * 100
            ok = dg <= INTENT_CM and dh <= INTENT_CM
            print(f'INTENT {clip} frame {key["f"]:>3}: grip off {dg:4.1f} cm, ring off {dh:4.1f} cm'
                  + ('' if ok else '  <-- FAIL'))
            if not ok:
                parts.append(f'staff misses its intent at frame {key["f"]}')
    cs = max((r['cloak_tear_cm'], r['step']) for r in T['rows'])
    warn = f' (WARN cloak opening {cs[0]:.1f} cm > {CLOAK_CM} at half-frame {cs[1]}: look at it)' if cs[0] > CLOAK_CM else ''
    bad |= bool(parts)
    print('GATE', clip, ('PASS' if not parts else 'FAIL: ' + '; '.join(parts)) + warn)
sys.exit(1 if bad else 0)
