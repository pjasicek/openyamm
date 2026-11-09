#!/usr/bin/env python3
"""Before/after of the demon's gates (review/gates_before vs review/gates_<tag>) -> review/gates_compare_<tag>.txt."""
import re, sys
tag = sys.argv[1]; A, B = 'review/gates_before', f'review/gates_{tag}'
def lines(d, f): return [l.rstrip() for l in open(f'{d}/{f}') if 'Unexpected' not in l and 'frozen site' not in l]
out = []
def cf(d):
    r = {}
    for l in lines(d, 'collapse.txt'):
        m = re.match(r'(\w+)\s+face-frames\s+(\d+)', l)
        if m: r[m[1]] = (int(m[2]), l.split('worst frame')[1].split('|')[0].strip() if 'worst frame' in l else '')
    return r
a, b = cf(A), cf(B); out.append('COLLAPSE face-frames installed -> reduced (sum %d -> %d)' % (sum(v[0] for v in a.values()), sum(v[0] for v in b.values())))
for k in a: out.append(f'  {k:13s} {a[k][0]:6d} -> {b.get(k, (0,))[0]:6d}')
def ah(d):
    return {l.split()[0]: l for l in lines(d, 'arm_hand.txt') if ' L: ' in l}
a, b = ah(A), ah(B); out.append('ARM/HAND (outer, exact) differing clips:')
for k in a:
    if a[k] != b.get(k): out.append(f'  before {a[k]}\n  after  {b.get(k)}')
for f in ('jitter.txt',):
    out.append('JITTER ' + [l for l in lines(A, f) if 'JITTER' in l][-1] + ' -> ' + [l for l in lines(B, f) if 'JITTER' in l][-1])
    fa = [l.split()[0] for l in lines(A, f) if 'FAIL' in l]; fb = [l.split()[0] for l in lines(B, f) if 'FAIL' in l]; out.append(f'  failing clips {fa} -> {fb}')
for f in ('detached.txt', 'flat.txt', 'bone_length.txt', 'winding.txt', 'texture_quality.txt'):
    try:
        out.append(f'{f}:\n  before ' + '\n  before '.join(l for l in lines(A, f) if 'shallow' not in l and 'root lift' not in l and not l.startswith('  part')) +
                   '\n  after  ' + '\n  after  '.join(l for l in lines(B, f) if 'shallow' not in l and 'root lift' not in l and not l.startswith('  part')))
    except FileNotFoundError as e:
        out.append(f'{f}: missing {e}')
da = {re.sub(r'part \d+ ', '', l.split(':')[0]).strip(): l for l in lines(A, 'detached.txt') if l.startswith('  part')}
db = {re.sub(r'part \d+ ', '', l.split(':')[0]).strip(): l for l in lines(B, 'detached.txt') if l.startswith('  part')}
out.append('DETACHED pieces before / after:'); out += ['  B ' + l.strip()[:170] for l in da.values()]; out += ['  A ' + l.strip()[:170] for l in db.values()]
open(f'review/gates_compare_{tag}.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
