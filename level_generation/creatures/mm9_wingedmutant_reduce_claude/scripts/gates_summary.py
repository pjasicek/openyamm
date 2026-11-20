#!/usr/bin/env python3
"""Before/after summary of review/gates_<a> and review/gates_<b> (gates.sh): one line per gate, worst values.
Usage: gates_summary.py <tag a> <tag b>"""
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'review'


def txt(tag, f):
    p = R / f'gates_{tag}' / f
    return p.read_text() if p.exists() else ''


def worst(tag):
    out = {}
    t = txt(tag, 'skirt.txt'); out['skirt through (cm, worst clip)'] = max(((float(m[1]), m[0]) for m in re.findall(r'^(\w+)\s+frames through.*max\s+([\d.]+) cm', t, re.M)), default=None)
    t = txt(tag, 'skirt_bunch.txt'); out['skirt faces<50% (max)'] = max((int(x) for x in re.findall(r'faces<50%:\s+(\d+)', t)), default=None)
    for f, k in (('arm_hand.txt', 'arm/hand'), ('arm_hand_skin.txt', 'arm/hand skin')):
        t = txt(tag, f); out[k + ' hand cm max'] = max((float(x) for x in re.findall(r'hand ([\d.]+)cm', t)), default=None)
        out[k + ' forearm cm max'] = max((float(x) for x in re.findall(r'forearm ([\d.]+)cm', t)), default=None)
    t = txt(tag, 'jitter.txt'); m = re.search(r'JITTER fails (\d+)', t); out['jitter fails'] = int(m[1]) if m else None
    out['jitter FAIL lines'] = [l.split()[0] for l in t.splitlines() if 'FAIL' in l]
    t = txt(tag, 'grip.txt'); out['grip inside cm max'] = max((float(x) for x in re.findall(r'max\s+([\d.]+) cm', t)), default=None)
    t = txt(tag, 'blade.txt'); out['blade worst cm'] = max((float(x) for x in re.findall(r"'worst_cm': ([\d.]+)", t)), default=None)
    t = txt(tag, 'rim.txt'); out['rim helmet cm max'] = max((float(x) for x in re.findall(r'helmet/horns\s+([\d.]+) cm', t)), default=None)
    out['rim face/beard cm max'] = max((float(x) for x in re.findall(r'face/beard\s+([\d.]+) cm', t)), default=None)
    t = txt(tag, 'beard.txt'); out['beard stretch max'] = max((float(x) for x in re.findall(r' (\d\.\d\d)', t)), default=None)
    t = txt(tag, 'wrist_gap.txt'); out['wrist gap opens cm max'] = max((float(x) for x in re.findall(r'opens \+?(-?[\d.]+) cm', t)), default=None)
    t = txt(tag, 'collapse.txt'); out['collapse face-frames sum'] = sum(int(x) for x in re.findall(r'face-frames\s+(\d+)', t))
    out['collapse exposed sum'] = sum(int(x) for l in t.splitlines() if '| exposed' in l for x in re.findall(r'=(\d+)', l.split('| exposed')[1]))
    for f in ('bone_length.txt', 'detached.txt', 'flat.txt', 'winding.txt', 'texture_quality.txt', 'handedness.txt'):
        out[f] = ' / '.join(l.strip() for l in txt(tag, f).splitlines()[-3:])[:200]
    t = txt(tag, 'orient.txt'); out['orient head mean max'] = max((float(x) for x in re.findall(r'Head fwd ([\d.]+)/', t)), default=None)
    return out


a, b = worst(sys.argv[1]), worst(sys.argv[2])
for k in a:
    print(f'{k:32s} {sys.argv[1]}: {a[k]}\n{"":32s} {sys.argv[2]}: {b[k]}')
