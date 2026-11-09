import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
g = np.load(HERE / 'work' / 'glb_parts.npz'); jn = g['jnames']
for c in np.unique(g['comp']):
    m = g['comp'] == c
    u, k = np.unique(g['joint'][m], return_counts=True); o = np.argsort(-k)[:3]
    C = g['cen'][m]
    print(f"comp {c:6d} n {m.sum():5d} head {int(g['head'][m].sum()):5d} hand {int(g['hand'][m].sum()):4d} lined {int(g['lined'][m].sum()):5d} tiny {int((g['uvarea'][m]<0.5).sum()):5d}",
          'lo', C.min(0).round(2), 'hi', C.max(0).round(2), [(jn[u[i]].replace('Bip01 ', ''), int(k[i])) for i in o])
