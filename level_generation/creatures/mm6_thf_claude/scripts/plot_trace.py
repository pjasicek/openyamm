#!/usr/bin/env python3
"""Plot work/trace_<clip>.json (trace_clip.py): joint/prop paths in front, side and top projections (shoulder, elbow,
wrist and dagger grip/tip per side, frame numbers every 4 half-frames, the arm drawn as a skeleton at the native
keys) and time series of the metrics with the gate lines. Needs matplotlib (scratchpad venv). Args: clip ->
review/trace_<clip>.png"""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = Path(__file__).resolve().parent.parent
clip = sys.argv[1]
T = json.load(open(HERE / 'work' / f'trace_{clip}.json'))
rows = T['rows']; n = len(rows); t = np.arange(n)
KEYS = [0, 6, 12, 18, 24, 30, 36] if clip == 'Attack' else []
COL = {'R': ('tab:red', 'tab:orange'), 'L': ('tab:blue', 'tab:cyan')}
fig = plt.figure(figsize=(20, 15))
views = [('front (X right = his left, Z up)', 0, 2, 1), ('side (from his right; -Y = forward to the left)', 1, 2, -1),
         ('top (X, Y; forward = down)', 0, 1, 1)]
for vi, (title, a, b, flip) in enumerate(views):
    ax = fig.add_subplot(2, 3, vi + 1)
    for k in 'RL':
        P = {j: np.array([r[k][j] for r in rows]) for j in ('shoulder', 'elbow', 'wrist', 'grip', 'tip')}
        X = lambda arr: arr[:, a] * flip
        ax.plot(X(P['wrist']), P['wrist'][:, b], '-', color=COL[k][0], lw=2, label=f'{k} wrist')
        ax.plot(X(P['tip']), P['tip'][:, b], '--', color=COL[k][1], lw=1.5, label=f'{k} dagger tip')
        ax.plot(X(P['elbow']), P['elbow'][:, b], ':', color=COL[k][0], lw=1, label=f'{k} elbow')
        for i in range(0, n, 4):
            ax.annotate(str(i), (X(P['wrist'])[i], P['wrist'][i, b]), fontsize=7, color=COL[k][0])
        for i in KEYS:
            if i < n:
                pts = np.array([P['shoulder'][i], P['elbow'][i], P['wrist'][i]])
                ax.plot(pts[:, a] * flip, pts[:, b], '-o', color='0.4', lw=1, ms=3)
                ax.plot([P['grip'][i, a] * flip, P['tip'][i, a] * flip], [P['grip'][i, b], P['tip'][i, b]], '-', color='k', lw=2)
    ax.set_title(f'{clip}: {title}'); ax.set_aspect('equal'); ax.grid(alpha=0.3)
    if vi == 0:
        ax.legend(fontsize=7, loc='lower left')
metrics = [('wrist_gap_mm', 'wrist seam gap (mm)', 3), ('ring_drift_mm', 'hand ring drift in forearm frame (mm)', 8),
           ('wrist_swing', 'wrist swing (deg)', 45), ('wrist_twist', 'wrist twist (deg)', 45),
           ('forearm_twist', 'forearm twist (deg)', 90), ('hand_turn_deg', 'hand turn per half-frame (deg)', 45),
           ('tip_speed', 'dagger tip travel per half-frame (m)', None)]
ax = fig.add_subplot(2, 3, (4, 6))
for k in 'RL':
    for j, (m, label, gate) in enumerate(metrics):
        v = np.array([r[k][m] for r in rows], float)
        if m == 'hand_turn_deg':
            v = np.minimum(v, 360 - v)
        if m == 'tip_speed':
            v = v * 300
        ax.plot(t, v + 0 * j, label=f'{k} {label}' + (' (x300)' if m == 'tip_speed' else ''),
                color=plt.cm.tab10(j), ls='-' if k == 'R' else '--')
cs = np.array([r['cloak_stretch'] for r in rows]) * 20
ax.plot(t, cs, color='k', lw=1, label='cloak max edge stretch (x20)')
for g, c in ((45, 'r'), (60, 'm'), (90, 'k')):
    ax.axhline(g, color=c, lw=0.5, ls=':')
for i in KEYS:
    ax.axvline(i, color='0.6', lw=0.5)
ax.set_xlabel('half-frame (48 fps); vertical lines = native keys'); ax.grid(alpha=0.3)
ax.legend(fontsize=7, ncol=3, loc='upper right')
plt.tight_layout()
out = HERE / 'review' / f'trace_{clip}.png'
plt.savefig(out, dpi=70)
print('PLOT', out)
