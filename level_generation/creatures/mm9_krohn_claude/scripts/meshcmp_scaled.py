"""Height-normalised mesh comparison: KROHN.abc (2.78 m, a giant) scaled to each other body's height and centred, p90/max
vertex-to-vertex distance in cm per region (mm9_meshcmp.py's loader). Usage: python3 meshcmp_scaled.py stem1,stem2,..."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'level_generation/creatures/claude_shared'))
import mm9_meshcmp as mc

def pts(stem):
    _, p, r, _ = mc.load(stem)
    return p / mc.CM, r

ka, kr = pts('krohn')
model = mc.abc.read_abc(mc.find_model('krohn'))
# drop the spear and sword pieces
n = 0; mask = []
for pc in model.pieces:
    k = len(pc.lods[0].vertices); mask += [pc.name not in ('sword', 'spear')] * k
mask = np.array(mask)
ka, kr = ka[mask], kr[mask]
for stem in sys.argv[1].split(','):
    b, br = pts(stem)
    s = (b[:, 1].max() - b[:, 1].min()) / (ka[:, 1].max() - ka[:, 1].min())
    a = ka * s
    a += (np.median(b, 0) - np.median(a, 0))
    d, _ = cKDTree(b).query(a)
    d *= mc.CM
    out = [f'{reg} p90 {np.percentile(d[kr == reg], 90):.1f} max {d[kr == reg].max():.1f}' for reg in mc.REGIONS if (kr == reg).any()]
    print(f'krohn x{s:.3f} vs {stem}: ' + ' | '.join(out))
