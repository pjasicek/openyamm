#!/usr/bin/env python3
"""Gate over work/trace_<clip>.json (trace_clip.py, 48 fps as the viewer plays): per clip and side the worst wrist
seam gap, hand-ring drift in the forearm frame, wrist swing / twist, forearm twist, hand turn per half-frame, and the
widest cloak tear (an edge stretched > 2x, by its opening in cm). When work/<clip>_intent.json exists (attack_thf.py writes the attack's), each key's played wrist position and blade
direction are compared with the intent. Args: clip ... Exit 1 when an arm/hand limit is exceeded; the cloak opening is a warning (stretched cloth between
chains reads as cloth, check the frame visually)."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
LIMITS = {'wrist_gap_mm': 3.0, 'ring_drift_mm': 8.0, 'wrist_swing': 45.0, 'wrist_twist': 45.0, 'forearm_twist': 90.0,
          'hand_turn_deg': 45.0}
INTENT_CM, INTENT_DEG = 5.0, 35.0   # played wrist / blade vs work/<clip>_intent.json at each key
CLOAK_CM = 3.0       # a ratio is meaningless on the 6 mm ragged-hem edges (5-6x between chains 17 cm apart); a
                     # tear is an edge stretched > 2x that opened by more than 3 cm
bad = False
for clip in sys.argv[1:]:
    T = json.load(open(HERE / 'work' / f'trace_{clip}.json'))
    parts = []
    for k in 'RL':
        for m, lim in LIMITS.items():
            v = max(((min(r[k][m], 360 - r[k][m]) if m == 'hand_turn_deg' else abs(r[k][m])), r['step']) for r in T['rows'])
            flag = v[0] > lim
            bad |= flag
            if flag:
                parts.append(f'{k} {m} {v[0]:.1f} > {lim} at half-frame {v[1]}')
    cs = max((r['cloak_tear_cm'], r['step']) for r in T['rows'])
    warn = f' (WARN cloak stretch opening {cs[0]:.1f} cm > {CLOAK_CM} at half-frame {cs[1]}: look at it)' \
        if cs[0] > CLOAK_CM else ''
    intent = HERE / 'work' / f'{clip.lower()}_intent.json'
    if intent.exists():                 # intent vs what the viewer plays: wrist target and blade direction per key
        import numpy as np
        rows = {r['step']: r for r in T['rows']}
        for key in json.load(open(intent))['keys']:
            r = rows.get(int(round(key['frame'] * T['fps'] / 24)))
            for k in 'RL':
                want = key[k]
                if r is None or want is None:
                    continue
                dw = float(np.linalg.norm(np.array(r[k]['wrist']) - np.array(want['wrist']))) * 100
                b = np.array(r[k]['tip']) - np.array(r[k]['grip']); b /= np.linalg.norm(b)
                wb = np.array(want['blade']); wb /= np.linalg.norm(wb)
                ang = float(np.degrees(np.arccos(np.clip(b @ wb, -1, 1))))
                ok = dw <= INTENT_CM and ang <= INTENT_DEG
                print(f'INTENT {clip} frame {key["frame"]:>4} {k}: wrist off {dw:4.1f} cm, blade off {ang:5.1f} deg'
                      + ('' if ok else '  <-- FAIL'))
                if not ok:
                    bad = True; parts.append(f'{k} misses its intent at frame {key["frame"]}')
    print('GATE', clip, ('PASS' if not parts else 'FAIL: ' + '; '.join(parts)) + warn)
sys.exit(1 if bad else 0)
