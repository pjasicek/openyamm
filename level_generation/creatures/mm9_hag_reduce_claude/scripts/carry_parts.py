#!/usr/bin/env python3
"""Old Hag (2026-11-05): carry Yrsa's per-face part labels (../mm9_yrsa_reduce_claude/work/glb_parts.npz, matched 1:1 to Yrsa's
final master there) to the Hag's installed LOD0 -> work/glb_parts.npz in the same layout.
The Hag is Yrsa's body with the bead parts deleted and the sleeves flared (mm9_hag_claude/scripts/hag_geo.py, no new topology),
re-UV'd by the texture pass. Measured: body primitive face i = Yrsa's face i (2,993 faces at identical centroids, the other 382
flared-sleeve faces at the same index with identical joint sets); head primitive faces map by centroid (all 5,102 exact, in order;
199 bead faces gone). Corner order per face is checked by vertex weights. Twins (outer GLB vertex -> its lining GLB vertex) are
rebuilt through each lined face's corners and its paired lining face's corners."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
Y = HERE.parent / 'mm9_yrsa_reduce_claude'
_, _, _, H = glbio.load(HERE / 'before' / 'mm9_hag.glb', 'Hag')
_, _, _, S = glbio.load(Y / 'before' / 'mm9_yrsa.glb', 'Yrsa')
g = dict(np.load(Y / 'work' / 'glb_parts.npz'))
hb, hh, yb, yh = H['Hag'], H['HagHead'], S['Yrsa'], S['YrsaHead']
assert len(hb['T']) == len(yb['T'])
d, nn = cKDTree(yh['P'][yh['T']].mean(1)).query(hh['P'][hh['T']].mean(1)); assert d.max() < 1e-6 and (np.diff(nn) > 0).all()
fmap = np.concatenate([np.arange(len(hb['T'])), len(yb['T']) + nn])           # Hag face -> Yrsa face
# corner order: per-corner weights and joints identical
for a, b, m in ((hb, yb, np.arange(len(hb['T']))), (hh, yh, nn)):
    wa = a['W'][a['T']]; wb = b['W'][b['T'][m]]; ja = a['J'][a['T']]; jb = b['J'][b['T'][m]]
    assert np.abs(wa - wb).max() < 1e-6 and (ja == jb).all(), 'corner order differs'
nfh = len(fmap); out = {}
for k in ('mat', 'hand', 'head', 'joint', 'comp', 'part', 'lined', 'lining', 'unmatched'):
    out[k] = g[k][fmap]
out['jnames'] = g['jnames']
out['cen'] = np.concatenate([hb['P'][hb['T']].mean(1), hh['P'][hh['T']].mean(1)])
out['voff'] = np.array([0, len(hb['P']), len(hb['P']) + len(hh['P'])]); out['foff'] = np.array([0, len(hb['T']), nfh])
inv = -np.ones(len(g['part']), np.int64); inv[fmap] = np.arange(nfh)
pair = g['pair'][fmap]; ok = pair >= 0; pair[ok] = inv[pair[ok]]; assert (pair[ok] >= 0).all()
out['pair'] = pair
# twins: Yrsa twin per Yrsa GLB vertex (prim-local index); rebuild per Hag vertex through face corners
twin = -np.ones(out['voff'][-1], np.int64); ambig = np.zeros(out['voff'][-1], bool)
yvoff = g['voff']
multi = {}
for pi, (a, b) in enumerate(((hb, yb), (hh, yh))):
    fo = out['foff'][pi]; tw_y = g['twin'][yvoff[pi]:yvoff[pi + 1]]
    for fh in np.flatnonzero(out['lined'][fo:out['foff'][pi + 1]]):
        F = fo + fh; p = pair[F]
        if p < 0:
            continue
        fy = fmap[F] - g['foff'][pi]; py = fmap[p] - g['foff'][pi]
        for c in range(3):
            u = tw_y[b['T'][fy, c]]
            if u < 0:
                continue
            cc = np.flatnonzero(b['T'][py] == u)
            if len(cc) != 1:
                continue
            hv = a['T'][fh, c]; ht = a['T'][p - fo, cc[0]]
            if twin[out['voff'][pi] + hv] >= 0 and twin[out['voff'][pi] + hv] != ht:
                ambig[out['voff'][pi] + hv] = True
            twin[out['voff'][pi] + hv] = ht; multi.setdefault(out['voff'][pi] + hv, set()).add(int(ht))
out['twin'] = twin; out['ambig'] = ambig
# the Hag's texture-pass UVs split the lining at seams the outer cloth does not have: an outer vertex can have several lining
# twins (same position and weights, other UV islands); mpqem.py picks per re-emitted face the combination with the smallest UV
# triangle (one island)
twins = -np.ones((len(twin), max(len(v) for v in multi.values())), np.int64)
for v, us in multi.items():
    twins[v, :len(us)] = sorted(us)
out['twins'] = twins
# every corner of a lined face with a pair must have a twin (mpqem asserts it for cut faces)
miss = 0
for pi, a in enumerate((hb, hh)):
    fo, fe = out['foff'][pi], out['foff'][pi + 1]; tw = twin[out['voff'][pi]:out['voff'][pi + 1]]
    L = out['lined'][fo:fe] & (pair[fo:fe] >= 0)
    miss += int((tw[a['T'][L]] < 0).any(1).sum())
print('faces', nfh, 'beads dropped', len(g['part']) - nfh, 'lined', int(out['lined'].sum()), 'lining', int(out['lining'].sum()),
      'twins', int((twin >= 0).sum()), 'ambiguous', int(ambig.sum()), 'lined faces missing a twin', miss)
print('dropped Yrsa faces by part', {int(k): int(v) for k, v in zip(*np.unique(g['part'][np.setdiff1d(np.arange(len(g['part'])), fmap)],
                                                                           return_counts=True))})
np.savez(HERE / 'work' / 'glb_parts.npz', **out)
