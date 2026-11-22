import sys, numpy as np
sys.path.insert(0, sys.path[0])
from pglb import load, lod0_body
g, m, names = load(sys.argv[1])
prim, dom = lod0_body(m)
P = prim['positions']
sel = P[:, 1] > 1.42
Q = P[sel]
print('slice z | all: ymin ymax | |x|>0.035: ymin ymax xmax | midline |x|<0.02 ymax')
for z in np.arange(-0.38, 0.17, 0.02):
    s = Q[(Q[:, 2] >= z) & (Q[:, 2] < z + 0.02)]
    if not len(s): continue
    side = s[np.abs(s[:, 0] + 0.009) > 0.035]
    mid = s[np.abs(s[:, 0] + 0.009) < 0.02]
    print(f'{z:+.2f} | {s[:,1].min():.3f} {s[:,1].max():.3f} | ' + (f'{side[:,1].min():.3f} {side[:,1].max():.3f} {np.abs(side[:,0]+0.009).max():.3f}' if len(side) else '-') + ' | ' + (f'{mid[:,1].max():.3f}' if len(mid) else '-'))
print('horizontal slices y: z range, half-width')
for y in np.arange(1.42, 1.92, 0.03):
    s = Q[(Q[:, 1] >= y) & (Q[:, 1] < y + 0.03)]
    if not len(s): continue
    print(f'{y:.2f} z {s[:,2].min():+.3f}..{s[:,2].max():+.3f}  hw {np.abs(s[:,0]+0.009).max():.3f}')
