#!/usr/bin/env python3
"""One line per gate and design, installed (review/gates_before) -> candidate (review/gates_<tag>). Usage: gate_summary.py <tag>"""
import json, re, sys
from pathlib import Path
tag = sys.argv[1]
def rd(t, n, f):
    p = Path(f'review/gates_{t}/d{n}/{f}'); return p.read_text() if p.exists() else ''
def ah(s):
    fr = [int(x) for x in re.findall(r'\((\d+)f>1cm\)', s)]; fa = [float(x) for x in re.findall(r'forearm ([\d.]+)cm', s)]
    fi = [float(x) for x in re.findall(r'fingers \[[\d.]+, ([\d.]+)\]', s)]
    return f'frames>1cm {sum(fr)}, forearm max {max(fa or [0])} cm, finger stretch max {max(fi or [0])}'
def robe(s):
    return 'max cm ' + ' '.join(f'{c[:4]}:{v}' for c, v in re.findall(r'^(\w+)\s+legs through robe\s+\d+/\d+ ([\d.]+) cm', s, re.M))
def sp(s): return f"max poke {max([float(x) for x in re.findall(r'poke ([\d.]+)mm', s)] or [0])} mm"
G = [('arm/hand', 'arm_hand_gate.txt', ah), ('jitter', 'jitter_gate.txt', lambda s: (re.findall(r'JITTER fails \d+', s) or ['?'])[0]),
     ('sleeve poke', 'sleeve_poke.txt', sp), ('robe', 'robe_gate.txt', robe),
     ('detached', 'detached.txt', lambda s: s.splitlines()[0].split(': ', 1)[-1] if s else '?'),
     ('flat', 'flat_shading.txt', lambda s: ' | '.join(re.findall(r'flat [\d.]+', s))),
     ('texture', 'texture_quality.txt', lambda s: ' | '.join(re.findall(r'atlas [\d.]+%|stretch p90 [\d.]+', s))),
     ('bones', 'bones.txt', lambda s: s.splitlines()[0].split('glb ')[-1] if s else '?'),
     ('winding', 'winding.txt', lambda s: s.strip().split(': ')[-1]), ('same clips', 'same_clips.txt', lambda s: s.split('|')[0].strip())]
for n in '1234':
    print(f'== d{n}')
    for name, f, fn in G:
        a, b = rd('before', n, f), rd(tag, n, f)
        print(f'  {name:11s} {fn(a) if a else "-"}  ->  {fn(b) if b else "-"}')
