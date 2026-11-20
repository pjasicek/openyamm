"""Vertex-level comparison of two MM9 ABC models: skeleton bind, topology, rigid offset, per-region residual."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools/mm9_import_discovery'))
from convert_abc_model import read_abc
import numpy as np
from scipy.spatial import cKDTree

D = Path(__file__).resolve().parents[4] / 'mm9/extracted/MODELS/MODELS'
CM = 2.56


def load(name):
    m = read_abc(D / name)
    P, B, PC = [], [], []
    for pc in m.pieces:
        l = pc.lods[0]
        for v in l.vertices:
            P.append(v.position)
            w = max(v.weights, key=lambda w: w.bias)
            B.append(m.nodes[w.node_index].name)
            PC.append(pc.name)
    return m, np.array(P, float), np.array(B), np.array(PC)


a, b = sys.argv[1], sys.argv[2]
ma, PA, BA, CA = load(a)
mb, PB, BB, CB = load(b)
print('pieces A', [(p.name, len(p.lods[0].vertices), len(p.lods[0].faces)) for p in ma.pieces])
print('pieces B', [(p.name, len(p.lods[0].vertices), len(p.lods[0].faces)) for p in mb.pieces])
na = [n.name for n in ma.nodes]
nb = [n.name for n in mb.nodes]
print('nodes', len(na), len(nb), 'same names', na == nb)
attrs = [x for x in dir(ma.nodes[0]) if not x.startswith('_')]
print('node attrs', attrs)
for key in ('transform', 'matrix', 'bind', 'bind_matrix', 'global_transform'):
    if key in attrs:
        diffs = [np.abs(np.array(getattr(x, key), float) - np.array(getattr(y, key), float)).max()
                 for x, y in zip(ma.nodes, mb.nodes)]
        print(key, 'max diff', max(diffs))
KB = cKDTree(PB)
d, idx = KB.query(PA)
print('A->B nearest vertex (cm): p50 %.2f p90 %.2f max %.2f' % (np.percentile(d, 50) * CM, np.percentile(d, 90) * CM, d.max() * CM))
for bone in sorted(set(BA)):
    m = BA == bone
    if m.sum() < 5:
        continue
    off = (PB[idx[m]] - PA[m]) * CM
    print('%-28s n=%4d d p50 %5.2f max %5.2f  mean off %s std %s' % (
        bone, m.sum(), np.median(d[m]) * CM, d[m].max() * CM, np.round(off.mean(0), 2), np.round(off.std(0), 2)))
