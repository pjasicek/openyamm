#!/usr/bin/env python3
"""Side by side of two gate runs (review/gates_<a>/, review/gates_<b>/): per clip the collapse worst regions, arm/hand and
forearm depth, jitter fails, skirt, cloth-torso, sword, grip, floor; then detached, bones, flat, texture quality, winding.
Usage: gate_compare.py <tag a> <tag b>"""
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'review'
a, b = sys.argv[1:3]
txt = lambda t, f: (R / f'gates_{t}' / f).read_text() if (R / f'gates_{t}' / f).exists() else ''


def per_clip(t, f, rx):
    out = {}
    for line in txt(t, f).splitlines():
        m = re.match(r'^(R |L )?\s*(\w+)\s+(.*)$', line)
        if m and re.search(rx, line):
            out[(m.group(1) or '') + m.group(2)] = m.group(3)
    return out


def coll(t):
    out = {}
    for line in txt(t, 'collapse.txt').splitlines():
        m = re.match(r'^(\w+)\s+face-frames\s+(\d+)\s+worst frame (.*?)\s+\|', line)
        if m:
            out[m.group(1)] = (int(m.group(2)), dict((k, int(v)) for k, v in re.findall(r'(\w+)=(\d+)', m.group(3))))
    return out


ca, cb = coll(a), coll(b)
print(f'COLLAPSE face-frames total {sum(v[0] for v in ca.values())} -> {sum(v[0] for v in cb.values())}; regions where {b} is worse by 3+ or reaches 20+:')
for clip in ca:
    ra, rb = ca[clip][1], cb.get(clip, (0, {}))[1]
    diffs = [f'{k} {ra.get(k, 0)}->{rb.get(k, 0)}' for k in sorted(set(ra) | set(rb)) if rb.get(k, 0) - ra.get(k, 0) >= 3 or (rb.get(k, 0) >= 20 and rb.get(k, 0) > ra.get(k, 0))]
    if diffs:
        print(f'  {clip:13s}', ', '.join(diffs))
for f, label in (('arm.txt', 'ARM (cloth)'), ('arm_skin.txt', 'ARM (skin)')):
    pa, pb = per_clip(a, f, r'hand .*cm@'), per_clip(b, f, r'hand .*cm@')
    num = lambda s: [float(x) for x in re.findall(r'(?:hand|forearm) (\d+\.\d)cm', s)]
    print(label, 'clips where hand/forearm depth (L hand, L forearm, R hand, R forearm) changes by 0.2+ cm:')
    for clip in pa:
        x, y = num(pa[clip]), num(pb.get(clip, ''))
        if len(x) == len(y) and any(abs(p - q) >= .2 for p, q in zip(x, y)):
            print(f'  {clip:13s} {x} -> {y}')
ja = re.findall(r'JITTER fails (\d+)', txt(a, 'jitter.txt')); jb = re.findall(r'JITTER fails (\d+)', txt(b, 'jitter.txt'))
print('JITTER fails', ja, '->', jb)
for line in txt(b, 'jitter.txt').splitlines():
    if 'FAIL' in line:
        clip = line.split()[0]; old = next((l for l in txt(a, 'jitter.txt').splitlines() if l.split()[:1] == [clip]), '')
        for side, seg in (('L', line.split('|')[0]), ('R', line.split('|')[1] if '|' in line else '')):
            if 'FAIL' in seg:
                osg = old.split('|')[0 if side == 'L' else 1] if old else ''
                print(f'  {clip} {side}:', re.findall(r'shoulder skin (-?[\d.]+)', osg), '->', re.findall(r'shoulder skin (-?[\d.]+)', seg), re.findall(r'upper arm ([\d.]+) deg/f ', osg), '->', re.findall(r'upper arm ([\d.]+) deg/f ', seg))
for f, rx, nm in (('skirt.txt', 'frames through', 'SKIRT'), ('cloth_torso.txt', 'skirt in torso', 'CLOTH-TORSO'), ('grip.txt', 'inside grip', 'GRIP')):
    pa, pb = per_clip(a, f, rx), per_clip(b, f, rx)
    ch = [(c, pa[c], pb.get(c)) for c in pa if pa[c] != pb.get(c)]
    print(nm, 'changed clips', len(ch), 'of', len(pa))
    for c, x, y in ch:
        print(f'  {c:13s} {x.strip()}\n  {"":13s} {(y or "").strip()}')
sa = dict(re.findall(r"^(\w+) \{'worst_cm': ([\d.]+)", txt(a, 'sword.txt'), re.M)); sb = dict(re.findall(r"^(\w+) \{'worst_cm': ([\d.]+)", txt(b, 'sword.txt'), re.M))
print('SWORD worst cm changed:', {c: (sa[c], sb.get(c)) for c in sa if sa[c] != sb.get(c)})
fa = dict(re.findall(r'^(\w+)\s+min\s+(-?[\d.]+) cm', txt(a, 'clip_floor.txt'), re.M)); fb = dict(re.findall(r'^(\w+)\s+min\s+(-?[\d.]+) cm', txt(b, 'clip_floor.txt'), re.M))
print('FLOOR min cm changed:', {c: (fa[c], fb.get(c)) for c in fa if fa[c] != fb.get(c)})
for f in ('detached.txt', 'bones.txt', 'flat.txt', 'texq.txt', 'winding.txt'):
    for t in (a, b):
        lines = [l for l in txt(t, f).splitlines() if l.strip() and 'Warning' not in l]
        print(f'{f[:-4].upper():9s} {t}:', ' / '.join(lines[-4:])[:600])
