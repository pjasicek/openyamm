"""Texture-aware quadric decimation (MeshLab) of the unprotected faces for each ladder ratio.
MeshLab's 'selected only' mode does not decimate with textures, so the unprotected part is cut out, decimated alone with
its cut edge preserved (boundary vertices stay put), and welded back to the untouched protected faces.
OBJ in/out because MeshLab needs a textured material per face for wedge UVs.
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
# natm: also every face above REA_PROTECT_ZMIN (metres), so the whole accepted head texture set stays unchanged
if os.environ.get('REA_PROTECT_ZMIN'):
    prot |= d['verts'][faces].mean(1)[:, 2] > float(os.environ['REA_PROTECT_ZMIN'])
TAG = os.environ.get('REA_TAG', 'r')
free = np.where(~prot)[0]
used = np.unique(faces[free]); remap = -np.ones(len(d['verts']), int); remap[used] = np.arange(len(used))
with open(f'{tmp}/in.obj', 'w') as f:
    f.write('mtllib in.mtl\n')
    f.writelines(f'v {x} {y} {z}\n' for x, y, z in d['verts'][used])
    f.writelines(f'vt {u} {v}\n' for u, v in wuv[free].reshape(-1, 2))
    f.write('usemtl m\n')
    f.writelines(f'f {remap[a]+1}/{3*i+1} {remap[b]+1}/{3*i+2} {remap[c]+1}/{3*i+3}\n'
                 for i, (a, b, c) in enumerate(faces[free]))


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


for r in ratios:
    ms = ml.MeshSet(); ms.load_new_mesh(f'{tmp}/in.obj')
    target = max(int(len(faces) * r) - int(prot.sum()), 200)
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=.3, extratcoordw=1.0,
        preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.save_current_mesh(f'{tmp}/out.obj', save_textures=False)
    v, f, w = read_obj(f'{tmp}/out.obj')
    # weld back: protected faces keep their original vertices; decimated vertices that coincide with an original
    # cut-edge vertex reuse it
    allv = np.concatenate([d['verts'], v]); off = len(d['verts'])
    from scipy.spatial import cKDTree  # noqa: E402
    dist, nearest = cKDTree(d['verts']).query(v)
    vid = np.where(dist < 1e-7, nearest, off + np.arange(len(v)))
    newf = np.concatenate([faces[prot], vid[f]])
    neww = np.concatenate([wuv[prot].reshape(-1, 2), w])
    keep = np.unique(newf); m2 = -np.ones(len(allv), int); m2[keep] = np.arange(len(keep))
    np.savez(f'{work}/mesh_{TAG}{int(r * 100)}.npz', verts=allv[keep], faces=m2[newf], wuv=neww)
    # cracks: open edges of the result that the source did not have (the cut edge must be closed by the weld)
    def open_edges(fs):
        e = np.sort(np.concatenate([fs[:, [0, 1]], fs[:, [1, 2]], fs[:, [2, 0]]]), 1)
        u, c = np.unique(e, axis=0, return_counts=True); return u[c == 1]
    oe_new, oe_src = len(open_edges(m2[newf])), len(open_edges(faces))
    print('DECIMATED', r, len(newf), 'faces (', int(prot.sum()), 'protected kept;', int((dist < 1e-7).sum()), 'welded )',
          'open edges', oe_new, 'source', oe_src)
