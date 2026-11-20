#!/usr/bin/env python3
"""Arm and hand gate summary of gates_glb.sh runs, side by side: per clip the G6 contacts (cm; pieces that touch,
shell counts and the floor clearance left out), hand stretch R/L, sole range, and the G4 arm stretch p99 maximum.
Usage: gate_summary.py <label> [label ...] -> review/shots/reduction/arm_hand_gate_reduction.json"""
import json, re, sys
out = {}
for label in sys.argv[1:]:
    r = {}; g4 = []
    for line in open(f'review/shots/reduction/gates_{label}.txt'):
        m = re.match(r'G6BOW (\w+) worst depth cm \(frame, piece hit\): (\{.*\})', line)
        if m:
            d = json.loads(m.group(2)); c = r.setdefault(m.group(1), {})
            c['g6_contacts_cm'] = {k: v[0] for k, v in d.items() if not k.endswith('_shell') and k != 'prop_floor'}
            c['axe_lowest_above_floor_cm'] = d['prop_floor'][0]
        m = re.match(r'HANDSTRETCH (\w+)\s+([RL]): max ([\d.]+)x', line)
        if m:
            r.setdefault(m.group(1), {})[f'hand_stretch_{m.group(2)}'] = float(m.group(3))
        m = re.match(r'SOLE (\w+): lowest foot per frame min ([-\d.]+) max ([-\d.]+) cm', line)
        if m:
            r.setdefault(m.group(1), {})['sole_cm'] = [float(m.group(2)), float(m.group(3))]
        m = re.match(r'G4 \S+\s+[RL]: stretch p99 ([\d.]+)', line)
        if m:
            g4.append(float(m.group(1)))
    r['G4_arm_stretch_p99_max'] = max(g4); out[label] = r
json.dump(out, open('review/shots/reduction/arm_hand_gate_reduction.json', 'w'), indent=1)
for clip in [k for k in out[sys.argv[1]] if k != 'G4_arm_stretch_p99_max']:
    print(clip.ljust(9), ' || '.join(f"{l}: G6 {out[l][clip]['g6_contacts_cm']} R {out[l][clip]['hand_stretch_R']} L {out[l][clip]['hand_stretch_L']} sole {out[l][clip].get('sole_cm')}" for l in out))
print('G4 p99 max', {l: out[l]['G4_arm_stretch_p99_max'] for l in out})
