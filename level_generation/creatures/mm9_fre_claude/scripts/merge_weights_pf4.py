#!/usr/bin/env python3
"""PF4: every PeasantF1 vertex keeps exactly PeasantF1's weights (weights_pf3.py run on F1's own asm, the approved model's rules), the
rows PF4 appended (decimated skirt lining, hood4, sleeve4) take weights_pf4.py's. Exception: F1's old hood ('scarf', now the hidden skull
under the new hood; its vertices on the face seam excepted) takes the weights of the nearest new-hood vertex: it lies 3 mm under the new
hood, whose cape rides on the bodice; on F1's weights its lappets (rigid head) poked through the cape in Standing (black patches in the
viewer) and its back (on Ponytail11/12) through the crown in Talk (a spike). Args: <F1 weights npz> <PF4 weights npz> <F1 asm npz> <out npz> [PF4 asm npz]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
a, b, A_, out = sys.argv[1:5]
Wa, Wb = np.load(a), np.load(b); n = len(np.load(A_)['co'])
assert list(Wa['wnames']) == list(Wb['wnames'])
wj, ww = Wb['wj'].copy(), Wb['ww'].copy(); wj[:n] = Wa['wj'][:n]; ww[:n] = Wa['ww'][:n]
moved = 0
if len(sys.argv) > 5:
    A = np.load(sys.argv[5]); co, comp = A['co'], A['comp']; names = [str(x) for x in A['names']]
    NW = len(Wb['wnames'])
    def dense(J, W):
        D = np.zeros((len(J), NW)); np.put_along_axis(D, J, W, 1); return D
    key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    onhead = np.zeros(inv.max() + 1, bool); onhead[inv[comp == names.index('head')]] = True
    sv = np.where((comp == names.index('scarf')) & ~onhead[inv])[0]; sv = sv[sv < n]      # the seam with the face keeps F1's weights
    if 'hair2' in names:      # Fre pass 4: the hidden skull lies under PeasantF2's hair cap (rigid on Head)
        hv = np.where((comp == names.index('hair2')) & ~A['hair2_tube'])[0]
    else:
        hv = np.where((comp == names.index('hood4')) & (A['f4_twin_v'] < 0))[0]
    _, j = cKDTree(co[hv]).query(co[sv])
    t = np.ones((len(sv), 1))
    D = dense(wj[sv], ww[sv]) * (1 - t) + dense(Wb['wj'][hv[j]], Wb['ww'][hv[j]]) * t
    o = np.argsort(-D, axis=1)[:, :4]; w4 = np.take_along_axis(D, o, 1); w4 /= np.maximum(w4.sum(1, keepdims=True), 1e-9)
    wj[sv] = o; ww[sv] = w4.astype(ww.dtype); moved = len(sv)
    if 'hair2' in names:
        # Fre pass 4 (r55 cap poke 4 mm from the rim: nape and below-ear face-shell vertices on F1's neck band came 3-5 mm through the
        # hair in Walking/Talk/Hit): face-shell rows (and their old-hood twins) the hair cap covers take the nearest cap row's weights too (rigid Head, the rim band
        # eased onto the skin in weights_fre.py), so what lies under the hair moves with it
        sys.path.insert(0, __file__.rsplit('/', 1)[0]); from geo4 import raycast
        C = np.array([0.0, 0.0, 0.665]); tri = A['tri']; capT = tri[np.isin(tri, hv).all(1)]
        nd = np.zeros(inv.max() + 1, int); np.add.at(nd, inv[comp == names.index('dress')], 1)
        q = np.where(np.isin(comp, [names.index('head'), names.index('scarf')]) & (co[:, 2] > 0.55) & (nd[inv] == 0))[0]      # with the old hood's seam twins; q = q[q < n]
        d = co[q] - C; r = np.linalg.norm(d, axis=1); u = d / r[:, None]; t = raycast(C + u * 0.6, -u, co, capT)
        qc = q[np.isfinite(t) & (0.6 - t > r)]
        _, j2 = cKDTree(co[hv]).query(co[qc]); wj[qc] = Wb['wj'][hv[j2]]; ww[qc] = Wb['ww'][hv[j2]]
        print('HAIR2 covered face-shell rows on the cap weights', len(qc))
np.savez(out, wj=wj, ww=ww, wnames=Wb['wnames']); print('MERGED', n, 'F1 rows kept,', len(wj) - n, 'PF4 rows; old-hood rows on the cape', moved)
