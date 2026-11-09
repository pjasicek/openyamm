"""Knight sword: texture-aware reduction per part (connected component of work/sword.npz, from prop_dump.py), each
part decimated on its own to its ratio, ratio 1 keeps it exactly. Parts by face count (the accepted round-2 sword):
868 grip wrap, 410 blade, 140 pommel, 132 guard, 116 grip core, 92 pommel ring, 68 guard collar, 63 pommel cap,
48 + 48 gems. Usage (venv with pymeshlab): sword_parts.py <tag> <faces>:<ratio>,...  (unlisted parts: DEFAULT ratio
0.5) -> work/sword_<tag>.npz (verts, faces, wuv, part) for prop_build.py, printed per-part counts and distance."""
import os
import sys

import numpy as np
import pymeshlab as ml
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.join(HERE, 'work')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prop_ladder_io import read_obj, write_obj  # noqa: E402

tag = sys.argv[1]
ratios = {int(k): float(v) for k, v in (kv.split(':') for kv in sys.argv[2].split(',') if kv)} if len(sys.argv) > 2 else {}
DEFAULT = float(os.environ.get('DEFAULT', '0.5'))
d = np.load(os.path.join(W, 'sword.npz'))
V, F, U = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
n = len(V); e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
comp = lab[F[:, 0]]
H = float(np.ptp(V, axis=0).max())
tmp = os.path.join(W, 'obj'); os.makedirs(tmp, exist_ok=True)
allv, allf, alluv, part, off = [], [], [], [], 0
for c in np.unique(comp):
    sel = np.where(comp == c)[0]; size = len(sel); r = ratios.get(size, DEFAULT)
    used = np.unique(F[sel]); remap = -np.ones(n, int); remap[used] = np.arange(len(used))
    pv, pf, puv = V[used], remap[F[sel]], U[sel].reshape(-1, 2)
    if r < 1:
        write_obj(os.path.join(tmp, 'in.obj'), pv, pf, puv)
        ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'in.obj')); ms.load_new_mesh(os.path.join(tmp, 'in.obj'))
        ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=max(int(size * r), 12), qualitythr=.3,
            extratcoordw=1.0, preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
        ms.save_current_mesh(os.path.join(tmp, 'out.obj'), save_textures=False)
        a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=5000)
        b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=5000)
        pv, pf, puv = read_obj(os.path.join(tmp, 'out.obj'))
        print(f'part {size:4d} -> {len(pf):4d}  max {max(a["max"], b["max"]) / H * 100:.3f} %  mean '
              f'{max(a["mean"], b["mean"]) / H * 100:.4f} % of the length')
    else:
        print(f'part {size:4d} kept')
    allv.append(pv); allf.append(pf + off); alluv.append(puv); part.append(np.full(len(pf), size)); off += len(pv)
faces = np.concatenate(allf)
np.savez(os.path.join(W, f'sword_{tag}.npz'), verts=np.concatenate(allv), faces=faces, wuv=np.concatenate(alluv),
         part=np.concatenate(part))
print('SWORD', tag, len(F), '->', len(faces))
