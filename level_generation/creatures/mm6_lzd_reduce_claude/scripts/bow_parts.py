"""Per-part texture-aware reduction of the bow (work/bow.npz, parts = work/bow_comp.npy connected components):
each part decimated on its own to its ratio (BOW_RATIOS=<comp>:<ratio>,...; unlisted parts kept), joined into
work/bow_<tag>.npz for prop_build.py. Prints per-part two-way Hausdorff (mm) and, for the grip wrap (BOW_GRIP comp),
the largest outward deviation from the source surface (the fist is fitted to it). Usage: bow_parts.py <tag>"""
import os, sys
import numpy as np
import struct, zlib
import pymeshlab as ml


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


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.join(HERE, 'work')
tag = sys.argv[1]
d = np.load(os.path.join(W, 'bow.npz')); comp = np.load(os.path.join(W, 'bow_comp.npy'))
V, F, U = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
ratios = {int(k): float(v) for k, v in (kv.split(':') for kv in os.environ['BOW_RATIOS'].split(','))}
grip = int(os.environ.get('BOW_GRIP', '2'))
tmp = os.path.join(W, 'obj'); os.makedirs(tmp, exist_ok=True)
allv, allf, allu, off = [], [], [], 0
for k in np.unique(comp):
    sel = np.where(comp == k)[0]; used = np.unique(F[sel]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    pv, pf, pu = V[used], remap[F[sel]], U[sel].reshape(-1, 2)
    if k in ratios:
        write_obj(os.path.join(tmp, 'in.obj'), pv, pf, pu)
        ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'in.obj')); ms.load_new_mesh(os.path.join(tmp, 'in.obj'))
        ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=max(int(len(sel) * ratios[k]), 12),
            qualitythr=.3, extratcoordw=1.0, preserveboundary=True, boundaryweight=10.0, optimalplacement=True,
            preservenormal=True)
        ms.save_current_mesh(os.path.join(tmp, 'out.obj'), save_textures=False)
        a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=20000)
        b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=20000)
        nv, nf, nu = read_obj(os.path.join(tmp, 'out.obj'))
        line = f'PART {k} {len(sel)} -> {len(nf)} hausdorff max {max(a["max"], b["max"]) * 1000:.2f} mm mean {max(a["mean"], b["mean"]) * 1000:.3f} mm'
        if k == grip:  # outward = new vertex outside the source surface along the source normal
            from scipy.spatial import cKDTree
            tri = pv[pf]; cen = tri.mean(1); nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
            dist, i = cKDTree(cen).query(nv, 4)
            out = np.einsum('vkc,vkc->vk', nv[:, None] - cen[i], nrm[i]).min(1)
            line += f'; grip outward max {out.max() * 1000:.2f} mm, p99 {np.percentile(out, 99) * 1000:.2f} mm'
        print(line)
        pv, pf, pu = nv, nf, nu
    allv.append(pv); allf.append(pf + off); allu.append(pu); off += len(pv)
v, f, u = np.concatenate(allv), np.concatenate(allf), np.concatenate(allu)
np.savez(os.path.join(W, f'bow_{tag}.npz'), verts=v, faces=f, wuv=u)
print('BOW', tag, len(F), '->', len(f))
