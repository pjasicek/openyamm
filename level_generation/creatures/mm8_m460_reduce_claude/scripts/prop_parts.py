"""Per-part texture-aware reduction of a held prop (work/<name>.npz from prop_dump.py, parts = connected components in
work/<name>_comp.npy): each listed part is decimated on its own to its ratio, every other part is kept exactly
(grip bar, straps, studs). Two-way surface distance in % of the longest dimension as in prop_ladder.py.
Usage (venv with pymeshlab): prop_parts.py <name> <tag> <part:ratio,...>  -> work/<name>_<tag>.npz"""
import os
import sys
import numpy as np
import pymeshlab as ml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prop_ladder_io import write_obj, read_obj  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.join(HERE, 'work')
name, tag, spec = sys.argv[1:4]
ratios = {int(k): float(v) for k, v in (kv.split(':') for kv in spec.split(','))}
d = np.load(os.path.join(W, f'{name}.npz')); lab = np.load(os.path.join(W, f'{name}_comp.npy'))
V, F, U = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
H = float(np.ptp(V, axis=0).max()); tmp = os.path.join(W, 'obj'); os.makedirs(tmp, exist_ok=True)


def sub(sel):
    used = np.unique(F[sel]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    return V[used], remap[F[sel]], U[sel].reshape(-1, 2)


kept = ~np.isin(lab, list(ratios))
parts = [sub(np.where(kept)[0])]
for c, r in ratios.items():
    v, f, u = sub(np.where(lab == c)[0])
    write_obj(os.path.join(tmp, 'in.obj'), v, f, u)
    ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'in.obj'))
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=max(int(len(f) * r), 12), qualitythr=.3,
        extratcoordw=1.0, preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.save_current_mesh(os.path.join(tmp, 'out.obj'), save_textures=False)
    parts.append(read_obj(os.path.join(tmp, 'out.obj')))
vs, fs, us, off = [], [], [], 0
for v, f, u in parts:
    vs.append(v); fs.append(f + off); us.append(u); off += len(v)
nv, nf, nu = np.concatenate(vs), np.concatenate(fs), np.concatenate(us)
# nkept: the first faces are the kept parts (prop_build.py keeps their transferred normals in angle mode)
np.savez(os.path.join(W, f'{name}_{tag}.npz'), verts=nv, faces=nf, wuv=nu, nkept=len(parts[0][1]))
write_obj(os.path.join(tmp, 'a.obj'), V, F, U.reshape(-1, 2)); write_obj(os.path.join(tmp, 'b.obj'), nv, nf, nu)
ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'a.obj')); ms.load_new_mesh(os.path.join(tmp, 'b.obj'))
a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=20000)
b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=20000)
print(f'{name} {tag}: {len(F)} -> {len(nf)} (kept {int(kept.sum())}) max {max(a["max"], b["max"]) / H * 100:.3f} % '
      f'mean {max(a["mean"], b["mean"]) / H * 100:.4f} %')
