#!/usr/bin/env python3
"""Head set faces of the merged mesh (EboraHead material), true-handed (x negated, the paint's frame): co, nor (smooth by
position), uv (head image 0..1), part (asm label: 0 skin, 1 hair, 3 horns, 4 fringe, 6 eyes, 7 ears, 9 mouth). Args: <mesh npz> <out npz>"""
import sys, numpy as np
D = np.load(sys.argv[1]); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; mn = [str(x) for x in D['matnames']]
t = tri[mat == mn.index('EboraHead')]; P = co * [-1, 1, 1]
fn = -np.cross(P[t[:, 1]] - P[t[:, 0]], P[t[:, 2]] - P[t[:, 0]])
key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[t[:, c]], fn)
N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
part = comp[t].max(1); c = P[t].mean(1)
# the scalp strip the removed hair tongue used to cover (between the fringe arms, above the forehead): paint it as hair
scalp = (part == 0) & (np.abs(c[:, 0]) < 0.024) & (c[:, 2] > 0.958) & (c[:, 1] < 0.08)
part[scalp] = 1; print('scalp faces relabelled hair', int(scalp.sum()))
# the 'ear' cards (part 7) are Meshy's side locks: 14 cm leaves from the temple to behind the jaw, 1-3 cm outside the skin,
# in front of the hair edge. The HD master and MM9 show hair there and no ears; the Codex views painted them hair (right
# view) or a small ear plus hair, and the skin label left a big skin flap over the hair (user, 2026-11-01: "the ear painted
# also on the hair"). Head fixes 3: painted, toned and tiered as hair
ear = part == 7; part[ear] = 1; print('ear cards relabelled hair', int(ear.sum()))
np.savez(sys.argv[2], co=P[t], nor=N[t], uv=uv[t], part=part, tri=t)
print('HEAD FACES', len(t))
