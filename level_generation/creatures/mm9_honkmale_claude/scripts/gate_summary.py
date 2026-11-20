#!/usr/bin/env python3
"""One-screen summary of review/gates/. Args: <project>"""
import json, re, sys
from pathlib import Path
R = Path(sys.argv[1]) / 'review/gates'
a = (R / 'arm_hand.txt').read_text().splitlines()
print('ARM/HAND')
for l in a:
    m = re.match(r'(\S+)\s+L: hand ([\d.]+)cm@\d+ \((\d+)f>1cm\).*fingers \[[\d.]+, ([\d.]+)\].*R: hand ([\d.]+)cm@\d+ \((\d+)f>1cm\).*fingers \[[\d.]+, ([\d.]+)\]', l)
    if m:
        print(f'  {m[1]:13} L {m[2]} cm ({m[3]}f) R {m[5]} cm ({m[6]}f) finger stretch {m[4]} / {m[7]}')
s = json.load(open(R / 'sleeve_gate.json'))
print('SLEEVE fps', s['fps'], s['views'])
for c, v in s['clips'].items():
    print(f'  {c:13}', {k: (x['poke_frames'], round(x['poke_max'], 3), {w: y['max_px'] for w, y in x['see'].items()}) for k, x in v.items()})
print('COLLAPSE')
for l in (R / 'collapse_gate.txt').read_text().splitlines()[1:]:
    print(' ', l[:300])
print('ROBE')
for k, v in json.load(open(R / 'robe_gate.json')).items():
    print(f"  {k:13} L {v['L']['frames']} R {v['R']['frames']} inner {v['inner']['frames']} (worst {v['inner']['worst']} edges at h {v['inner']['hmax']})")
print((R / 'jitter.txt').read_text().splitlines()[-1], '|', (R / 'winding.txt').read_text().strip(), '|', (R / 'flat.txt').read_text().strip()[:110])
print((R / 'detached.txt').read_text().splitlines()[0])
print((R / 'viewer_check.txt').read_text()[-120:].replace('\n', ' '))
