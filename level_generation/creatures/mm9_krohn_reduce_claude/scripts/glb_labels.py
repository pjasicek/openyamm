#!/usr/bin/env python3
"""Per installed LOD0 face (primitive order Krohn, KrohnHead, KrohnProps) the master's face labels (work/master_faces.npz from
dump_master.py: lined, head, hand, graft_s, graft_side) by rest centroid: Blender z-up -> glTF y-up, mirrored in x (mirror_glb.py),
offset fitted by medians. -> work/glb_labels.npz (mat, cen, lined, head, hand, graft, dist)"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_krohn.glb', 'Krohn')
m = np.load(HERE / 'work' / 'master_faces.npz')
c = m['Body__cen']; fc = np.c_[-c[:, 0], c[:, 2], -c[:, 1]]
out = dict(mat=[], cen=[], lined=[], head=[], hand=[], graft=[], dist=[], src=[])
for k, name in enumerate(['Krohn', 'KrohnHead', 'KrohnProps']):
    P, T = D[name]['P'], D[name]['T']; gc = P[T].mean(1)
    if name == 'KrohnProps':
        z = np.zeros(len(T)); out['mat'].append(np.full(len(T), k)); out['cen'].append(gc)
        out['src'].append(-np.ones(len(T), int))
        for key in ('lined', 'head', 'hand', 'graft', 'dist'):
            out[key].append(z)
        continue
    allg = np.concatenate([D[q]['P'] for q in ('Krohn', 'KrohnHead')])
    off = np.array([0.0, allg[:, 1].min() - fc[:, 1].min(), 0.0])     # the export lifted the lowest point to the floor
    d, nn = cKDTree(fc + off).query(gc)
    off = off + np.median(gc - (fc + off)[nn], 0); d, nn = cKDTree(fc + off).query(gc)
    print(name, len(T), 'offset', off.round(5), 'dist max', d.max().round(6), 'p99', np.percentile(d, 99).round(6), 'dup', len(nn) - len(np.unique(nn)))
    out['mat'].append(np.full(len(T), k)); out['cen'].append(gc); out['dist'].append(d)
    out['lined'].append(m['Body__f_lined'][nn]); out['head'].append(m['Body__f_head'][nn]); out['hand'].append(m['Body__f_hand'][nn])
    out['graft'].append(m['Body__v_graft_s'][nn]); out['src'].append(nn)
res = {k: np.concatenate(v) for k, v in out.items()}
for k in range(2):
    s = res['mat'] == k
    print(k, 'lined', int(res['lined'][s].sum()), 'head', int((res['head'][s] > 0).sum()), 'hand', int((res['hand'][s] > 0).sum()),
          'graft>0', int((res['graft'][s] > 0).sum()))
np.savez(HERE / 'work' / 'glb_labels.npz', **res)
