"""Overall ladder ratios that give the free body part (group 0, not kept) the requested ratios, with the group ratios
fixed. Usage: ladder_ratios.py <keep .npy> <groups .npy> <g:r,...> <body ratio,...>"""
import sys
import numpy as np
k = np.load(sys.argv[1]); g = np.load(sys.argv[2]); gr = {int(a): float(b) for a, b in (x.split(':') for x in sys.argv[3].split(','))}
n = len(k); fixed = k.sum() + sum(int(((g == a) & ~k).sum() * r) for a, r in gr.items())
free = ((~k) & ~np.isin(g, list(gr))).sum()
print(','.join(f'{(fixed + free * float(b)) / n:.4f}' for b in sys.argv[4].split(',')), f'# kept {int(k.sum())} free body {int(free)}')
