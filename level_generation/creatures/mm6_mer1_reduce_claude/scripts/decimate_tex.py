"""Texture-aware quadric decimation (MeshLab) of the unprotected faces for each ladder ratio.
MeshLab's 'selected only' mode does not decimate with textures, so the unprotected part is cut out, decimated alone with
its cut edge preserved (boundary vertices stay put), and welded back to the untouched protected faces.
OBJ in/out because MeshLab needs a textured material per face for wedge UVs.
With REA_PROTECT_HEAD=1 and REA_HEAD_RATIO=<r>, the head is decimated separately at r instead of kept.
Usage: decimate_tex.py <work dir> <ratio,...>  -> work/mesh_r<NN>.npz (verts, faces, wedge uv)"""
import os
import struct
import sys
import zlib
import numpy as np
import pymeshlab as ml

work, ratios = sys.argv[1], [float(r) for r in sys.argv[2].split(',')]
d = np.load(f'{work}/mesh_in.npz')
tmp = f'{work}/obj'; os.makedirs(tmp, exist_ok=True)
chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
open(f'{tmp}/tex.png', 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
                                    + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
open(f'{tmp}/in.mtl', 'w').write('newmtl m\nmap_Kd tex.png\n')
prot = (d['protect'] > .5) & (os.environ.get('REA_PROTECT_HEAD', '0') == '1')
faces, wuv = d['faces'], d['wuv'].reshape(-1, 3, 2)
free = np.where(~prot)[0]


def write_part(ids, path):
    """One face subset as a textured OBJ (wedge UVs), indices local to the subset."""
    used = np.unique(faces[ids]); remap = -np.ones(len(d['verts']), int); remap[used] = np.arange(len(used))
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x} {y} {z}\n' for x, y, z in d['verts'][used])
        f.writelines(f'vt {u} {v}\n' for u, v in wuv[ids].reshape(-1, 2))
        f.write('usemtl m\n')
        f.writelines(f'f {remap[a]+1}/{3*i+1} {remap[b]+1}/{3*i+2} {remap[c]+1}/{3*i+3}\n'
                     for i, (a, b, c) in enumerate(faces[ids]))


write_part(free, f'{tmp}/in.obj')
# REA_HEAD_RATIO: the protected (head) faces are decimated too, separately and gently, instead of kept; both parts keep
# their shared cut edge and weld back to the original vertices along it
HEAD_RATIO = float(os.environ.get('REA_HEAD_RATIO', '0') or 0)
if HEAD_RATIO > 0:
    write_part(np.where(prot)[0], f'{tmp}/head.obj')

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


def decimate(path, target):
    ms = ml.MeshSet(); ms.load_new_mesh(path)
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=max(target, 200), qualitythr=.3,
        extratcoordw=1.0, preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.save_current_mesh(f'{tmp}/out.obj', save_textures=False)
    return read_obj(f'{tmp}/out.obj')


from scipy.spatial import cKDTree  # noqa: E402
tree = cKDTree(d['verts'])
head_part = decimate(f'{tmp}/head.obj', int(prot.sum() * HEAD_RATIO)) if HEAD_RATIO > 0 else None
for r in ratios:
    if HEAD_RATIO > 0:
        parts = [decimate(f'{tmp}/in.obj', int(len(free) * r)), head_part]
        kept_f, kept_w = np.zeros((0, 3), int), np.zeros((0, 2))
    else:
        parts = [decimate(f'{tmp}/in.obj', int(len(faces) * r) - int(prot.sum()))]
        kept_f, kept_w = faces[prot], wuv[prot].reshape(-1, 2)
    # weld back: decimated vertices that coincide with an original cut-edge vertex reuse it
    allv, newf, neww, welded = [d['verts']], [kept_f], [kept_w], 0
    off = len(d['verts'])
    for v, f, w in parts:
        dist, nearest = tree.query(v)
        vid = np.where(dist < 1e-7, nearest, off + np.arange(len(v)))
        allv.append(v); newf.append(vid[f]); neww.append(w); off += len(v); welded += int((dist < 1e-7).sum())
    allv, newf, neww = np.concatenate(allv), np.concatenate(newf), np.concatenate(neww)
    keep = np.unique(newf); m2 = -np.ones(len(allv), int); m2[keep] = np.arange(len(keep))
    np.savez(f'{work}/mesh_r{int(r * 100)}.npz', verts=allv[keep], faces=m2[newf], wuv=neww)
    print('DECIMATED', r, len(newf), 'faces (', int(prot.sum()), 'protected,', f'head ratio {HEAD_RATIO};' if HEAD_RATIO else 'kept;',
          welded, 'welded )')
