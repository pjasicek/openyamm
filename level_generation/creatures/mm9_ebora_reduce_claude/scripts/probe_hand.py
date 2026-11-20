"""Which body face holds the deepest hand vertex (arm_hand_gate.py's sparse test, outer faces) at one clip time.
Usage: probe_hand.py <glb> <clip> <seconds> <side L|R>"""
import sys, runpy
from pathlib import Path
glb, clip, t, side = sys.argv[1:5]
sys.argv = ['arm_hand_gate.py', glb, '/dev/null', '--side', 'L= L ', '--side', 'R= R ', '--outer-only', '--clips', 'NONE']
src = Path(__file__).resolve().parents[1].parent / 'mm9_ebora_claude/scripts/arm_hand_gate.py'
code = src.read_text().split('\nfor clip')[0]   # setup only
g = {'__file__': str(src), '__name__': 'probe'}
sys.path.insert(0, str(src.parent))
exec(compile(code, str(src), 'exec'), g)
import numpy as np
from scipy.spatial import cKDTree
d = g['SID'][side]; w, X = g['posed'](clip, float(t)); tris = g['tris']
pts = X[d['hv']]; faces = d['body_f']
T = X[tris[faces]]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
S = np.einsum('kb,fbc->fkc', g['BARY'], T).reshape(-1, 3); N = np.repeat(n, 4, 0)
dist, i = cKDTree(S).query(pts, distance_upper_bound=0.06); ok = np.isfinite(dist)
v = pts[ok] - S[i[ok]]; behind = np.einsum('ij,ij->i', v, N[i[ok]]) < -0.7 * dist[ok]
dep = np.zeros(len(pts)); dep[np.where(ok)[0][behind]] = dist[ok][behind]
k = int(dep.argmax()); f = faces[i[k] // 4] if ok[k] else -1
# which primitive does face f belong to
offs = np.cumsum([0] + [len(pr['triangles']) for pr in [g['P'][q] for q in g['USE']]])
prim = int(np.searchsorted(offs, f, side='right') - 1)
print('max depth cm', round(dep.max() * 100, 2), 'body face', f, 'primitive', prim, 'dominant joints of its corners', [g['dom'][x] for x in tris[f]], 'hand vertex dom', g['dom'][d['hv'][k]])
