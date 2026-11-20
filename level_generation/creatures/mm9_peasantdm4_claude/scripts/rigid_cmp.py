"""Is PeasantDM4's mesh a rigidly shifted copy of a built dwarf? Translation-only ICP (and full rigid ICP) of DM4 onto
DM1/DM2/DM3 in MM9's ABC frame, then region p90 surface distances before/after. Run from tools/mm9_import_discovery/.
Args: <a> <b,...> (lower-case file stems)."""
import sys
sys.path.insert(0, '.')
import numpy as np
from scipy.spatial import cKDTree
SP = '/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/74ae08a0-ce66-4dda-8cb9-a8062f5327d4/scratchpad'
sys.path.insert(0, SP)
import meshcmp as mc

def stats(PA, RA, KB, PB, RB, KA, sh):
    dA = KB.query(PA + sh)[0] * mc.CM
    dB = KA.query(PB - sh)[0] * mc.CM
    out = {}
    for r in ('head', 'torso', 'arms', 'legs'):
        z = np.concatenate([dA[RA == r], dB[RB == r]])
        out[r] = (np.percentile(z, 50), np.percentile(z, 90), (z > 1.5).mean() * 100, z.max())
    return out

def fmt(o):
    return '  '.join(f"{r}: p50 {a:4.1f} p90 {p:4.1f} {q:3.0f}%>1.5 max {m:4.1f}" for r, (a, p, q, m) in o.items())

a = sys.argv[1]
PA, RA, TA, KA = mc.get(a)
for b in sys.argv[2].split(','):
    PB, RB, TB, KB = mc.get(b)
    print(f'== {a} vs {b}')
    print('  raw     ', fmt(stats(PA, RA, KB, PB, RB, KA, np.zeros(3))))
    for sel_name, sel in (('all', np.ones(len(PA), bool)), ('torso', RA == 'torso'), ('head', RA == 'head')):
        sh = np.zeros(3)
        for it in range(40):
            d, i = KB.query(PA[sel] + sh)
            # nearest surface sample points of B: tree data
            tgt = KB.data[i]
            sh = sh + np.median(tgt - (PA[sel] + sh), axis=0)
        print(f'  shift({sel_name}) = {sh*mc.CM} cm')
        print('  shifted ', fmt(stats(PA, RA, KB, PB, RB, KA, sh)))
