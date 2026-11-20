"""Bow ladder: the grip wrap (the left fist is fitted to it) and the six string-loop rings are kept exactly; each limb
is decimated on its own (texture-aware MeshLab collapse, prop_ladder.py settings) and checked with the two-way
Hausdorff distance against its source limb (% of the bow length; pass max <= 1.5 %, mean <= 0.15 %).
Usage (venv with pymeshlab): bow_ladder.py [ratio,...] -> work/bow_b<NN>.npz (prop_build.py input), printed table."""
import os, sys
import numpy as np
import pymeshlab as ml
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import struct, zlib

W = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work')
ratios = [float(r) for r in (sys.argv[1] if len(sys.argv) > 1 else '0.6,0.45,0.35,0.25').split(',')]
d = np.load(os.path.join(W, 'bow.npz')); V, F, U = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
H = float(np.ptp(V, axis=0).max())
n = len(V); r = np.concatenate([F[:, 0], F[:, 1], F[:, 2]]); c = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1][F[:, 0]]
size = np.bincount(lab)
limbs = [k for k in range(len(size)) if size[k] > 300 and np.ptp(V[np.unique(F[lab == k])][:, 1]) > 0.3]
kept = ~np.isin(lab, limbs)
tmp = os.path.join(W, 'obj'); os.makedirs(tmp, exist_ok=True)
print('bow', len(F), 'limbs', [int(size[k]) for k in limbs], 'kept', int(kept.sum()))


def write_obj(path, verts, faces, uv):
    """OBJ with one textured material: MeshLab's texture-aware collapse needs a texture per face."""
    folder = os.path.dirname(path)
    chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
    open(os.path.join(folder, 'tex.png'), 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
    open(os.path.join(folder, 'in.mtl'), 'w').write('newmtl m\nmap_Kd tex.png\n')
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x} {y} {z}\n' for x, y, z in verts)
        f.writelines(f'vt {u} {v}\n' for u, v in uv)
        f.write('usemtl m\n')
        f.writelines(f'f {a+1}/{3*i+1} {b+1}/{3*i+2} {c+1}/{3*i+3}\n' for i, (a, b, c) in enumerate(faces))


def read_obj(path):
    vs, vts, fs, fts = [], [], [], []
    for line in open(path):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            vs.append([float(x) for x in p[1:4]])
        elif p[0] == 'vt':
            vts.append([float(x) for x in p[1:3]])
        elif p[0] == 'f':
            idx = [q.split('/') for q in p[1:4]]
            fs.append([int(q[0]) - 1 for q in idx]); fts.append([int(q[1]) - 1 for q in idx])
    return np.array(vs), np.array(fs, np.int32), np.array(vts)[np.array(fts).reshape(-1)]


def part(sel):
    used = np.unique(F[sel]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    return V[used], remap[F[sel]], U[sel].reshape(-1, 2)


for ratio in ratios:
    pv, pf, pu, worst = [part(kept)[0]], [part(kept)[1]], [part(kept)[2]], (0, 0)
    off = len(pv[0])
    for k in limbs:
        lv, lf, lu = part(lab == k)
        write_obj(os.path.join(tmp, 'in.obj'), lv, lf, lu)
        ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'in.obj')); ms.load_new_mesh(os.path.join(tmp, 'in.obj'))
        ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=int(len(lf) * ratio), qualitythr=.3,
            extratcoordw=1.0, preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
        ms.save_current_mesh(os.path.join(tmp, 'out.obj'), save_textures=False)
        a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=20000)
        b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=20000)
        worst = (max(worst[0], a['max'], b['max']), max(worst[1], a['mean'], b['mean']))
        dv, df, duv = read_obj(os.path.join(tmp, 'out.obj'))
        pv.append(dv); pf.append(df + off); pu.append(duv); off += len(dv)
    out = dict(verts=np.concatenate(pv), faces=np.concatenate(pf), wuv=np.concatenate(pu))
    np.savez(os.path.join(W, f'bow_b{int(ratio * 100)}.npz'), **out)
    mx, mean = worst[0] / H * 100, worst[1] / H * 100
    print(f'b{int(ratio * 100)} total {len(out["faces"])} max {mx:.3f}% mean {mean:.4f}%',
          'PASS' if mx <= 1.5 and mean <= 0.15 else 'fail')
