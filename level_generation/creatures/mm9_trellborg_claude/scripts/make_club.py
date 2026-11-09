#!/usr/bin/env python3
"""Spiked club from MM9's stations (no Codex master for the shape, MM9's outline: brief lesson). Frame: t along MM9's axis from its centroid, u across the plank (spikes on -u), w the thickness. Grip section thinned to the fist's hole. Wood takes the left of a 1024 x 512 atlas by cylinder UVs, iron the right. Writes work/club.npz (V in (t, u, w), F, UV)."""
import numpy as np
GR = 0.0255                     # grip radius: the fist's free hole is 2.8 cm
#        t      centre u  half u  half w
ST = [(-0.893, 0.0, 0.010, 0.010), (-0.875, 0.0, 0.034, 0.034), (-0.84, 0.0, 0.043, 0.043), (-0.80, 0.0, 0.040, 0.040), (-0.765, 0.0, 0.031, 0.031), (-0.72, 0.0, GR, GR), (-0.635, 0.0, GR, GR),
      (-0.55, 0.0, GR, GR), (-0.50, 0.0, 0.034, 0.034), (-0.44, 0.0, 0.043, 0.047), (-0.30, 0.012, 0.070, 0.082), (-0.16, 0.035, 0.096, 0.118), (-0.08, 0.055, 0.112, 0.136), (0.05, 0.06, 0.116, 0.138),
      (0.22, 0.06, 0.118, 0.138), (0.37, 0.06, 0.118, 0.136), (0.415, 0.056, 0.090, 0.104), (0.445, 0.05, 0.040, 0.046), (0.457, 0.05, 0.006, 0.006)]
N = 14
V, UV, F = [], [], []
TMIN, TMAX = ST[0][0], ST[-1][0]
def add(p, q): V.append(p); UV.append(q); return len(V) - 1
# wood: u = around (0..1 twice over the left half, wood is seamless left-right on the wood part), v along
rows = []
for s in ST:
    r = []
    for k in range(N + 1):
        a = 2 * np.pi * k / N
        r.append(add((s[0], s[1] + s[2] * np.cos(a), s[3] * np.sin(a)), (0.5 * k / N * 0.97 + 0.005, 0.02 + 0.96 * (s[0] - TMIN) / (TMAX - TMIN))))
    rows.append(r)
for a, b in zip(rows[:-1], rows[1:]):
    for k in range(N):
        F += [(a[k], a[k + 1], b[k + 1]), (a[k], b[k + 1], b[k])]
# iron: nails, square shank + pyramid; the side row on -u, a hook at the tip on +u
def nail(t0, out, base, h, lean=0.0, bu=None):
    """base centre at (t0, bu); pointing `out` sign in u"""
    bw = base / 2
    corners = [(-bw, -bw), (bw, -bw), (bw, bw), (-bw, bw)]
    uc = bu; ring0 = [add((t0 + a, uc, b), (0.55 + 0.1 * (i % 2), 0.1)) for i, (a, b) in enumerate(corners)]
    ring1 = [add((t0 + a * 0.9, uc + out * h * 0.33, b * 0.9), (0.55 + 0.1 * (i % 2), 0.4)) for i, (a, b) in enumerate(corners)]
    tip = add((t0 + lean, uc + out * h, 0.0), (0.6, 0.9))
    for i in range(4):
        j = (i + 1) % 4
        if out > 0: F.extend([(ring0[i], ring1[i], ring1[j]), (ring0[i], ring1[j], ring0[j]), (ring1[i], tip, ring1[j])])
        else: F.extend([(ring0[i], ring1[j], ring1[i]), (ring0[i], ring0[j], ring1[j]), (ring1[i], ring1[j], tip)])
EDGE = lambda t: float(np.interp(t, [s[0] for s in ST], [s[1] - s[2] for s in ST]))
for t, tipu in ((-0.21, -0.11), (-0.10, -0.167), (0.036, -0.20), (0.18, -0.25), (0.32, -0.24)):
    b = EDGE(t) + 0.018
    nail(t, -1, 0.05, b - tipu, lean=-0.012, bu=b)
nail(0.33, 1, 0.055, 0.2, lean=-0.06, bu=0.165)
np.savez('work/club.npz', V=np.array(V, 'f8'), F=np.array(F, 'i4'), UV=np.array(UV, 'f4'))
print('CLUB verts', len(V), 'tris', len(F))
