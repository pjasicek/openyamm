"""Texture-aware quadric decimation (MeshLab) of the unprotected faces for each ladder ratio.
MeshLab's 'selected only' mode does not decimate with textures, so the unprotected part is cut out, decimated alone with
its cut edge preserved (boundary vertices stay put), and welded back to the untouched protected faces.
OBJ in/out because MeshLab needs a textured material per face for wedge UVs.
Protection: REA_PROTECT_HEAD=1 (Head/Jaw weights) or REA_PROTECT_FACES=<bool .npy per face>; REA_PROTECT_RATIO
decimates the protected part separately instead of keeping it. REA_KEEP_FACES=<bool .npy per face> is always kept
exactly (werewolf: necklace tube and pendant, which break at any cut). REA_GROUPS=<int .npy per face> with
REA_GROUP_RATIOS=1:0.6,2:0.5 decimates each labelled group on its own to its ratio (leather fighter: head and gloves);
label 0 takes the rest of the ladder budget.
Coincident vertices with different weights (MM8 Dragon: the split lip seam, upper on Head, lower on Jaw) are moved
2e-5 m apart towards their own faces for MeshLab and the weld-back, so each output vertex finds its own source
vertex; the npz records it (src_index, -1 for new vertices) and source vertices keep exact positions.
Usage: decimate_tex.py <work dir> <ratio,...>  -> work/mesh_r<NN>.npz (verts, faces, wedge uv, src_index)"""
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
if os.environ.get('REA_PROTECT_FACES'):  # explicit per-face protection (ghost: skull and eyes from the region mask)
    prot = np.load(os.environ['REA_PROTECT_FACES'])
# protected faces are kept, or decimated on their own to this ratio (cut edge preserved like the free part)
PROT_RATIO = float(os.environ.get('REA_PROTECT_RATIO', '1'))
kept = np.load(os.environ['REA_KEEP_FACES']) if os.environ.get('REA_KEEP_FACES') else np.zeros(len(d['faces']), bool)
prot = prot & ~kept
faces, wuv = d['faces'], d['wuv'].reshape(-1, 3, 2)
from scipy.spatial import cKDTree  # noqa: E402
pv = d['verts'].copy()
pairs = cKDTree(pv).query_pairs(1e-6, output_type='ndarray')
if len(pairs):
    cen = pv[faces].mean(1); acc = np.zeros_like(pv); cnt = np.zeros(len(pv))
    for k in range(3):
        np.add.at(acc, faces[:, k], cen); np.add.at(cnt, faces[:, k], 1)
    for i in np.unique(pairs):
        dv = acc[i] / max(cnt[i], 1) - pv[i]; pv[i] += 2e-5 * dv / (np.linalg.norm(dv) + 1e-12)
    print('SEPARATED', len(np.unique(pairs)), 'coincident vertices')


def write_obj(path, sel):
    used = np.unique(faces[sel]); remap = -np.ones(len(d['verts']), int); remap[used] = np.arange(len(used))
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x} {y} {z}\n' for x, y, z in pv[used])
        f.writelines(f'vt {u} {v}\n' for u, v in wuv[sel].reshape(-1, 2))
        f.write('usemtl m\n')
        f.writelines(f'f {remap[a]+1}/{3*i+1} {remap[b]+1}/{3*i+2} {remap[c]+1}/{3*i+3}\n'
                     for i, (a, b, c) in enumerate(faces[sel]))


groups = np.load(os.environ['REA_GROUPS']) if os.environ.get('REA_GROUPS') else np.zeros(len(faces), int)
gratios = {int(k): float(v) for k, v in (kv.split(':') for kv in os.environ.get('REA_GROUP_RATIOS', '').split(',') if kv)}
gsel = {g: np.where((groups == g) & ~prot & ~kept)[0] for g in gratios}
gsel = {g: sel for g, sel in gsel.items() if len(sel)}  # a group fully kept or empty
for g, sel in gsel.items():
    write_obj(f'{tmp}/group{g}.obj', sel)
gbudget = sum(int(len(sel) * gratios[g]) for g, sel in gsel.items())
free = np.where(~prot & ~kept & ~np.isin(groups, list(gratios)))[0]
write_obj(f'{tmp}/in.obj', free)
if PROT_RATIO < 1:
    write_obj(f'{tmp}/prot.obj', np.where(prot)[0])


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


def decimate(obj, target):
    ms = ml.MeshSet(); ms.load_new_mesh(obj)
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=.3, extratcoordw=1.0,
        preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.save_current_mesh(f'{tmp}/out.obj', save_textures=False)
    return read_obj(f'{tmp}/out.obj')


tree = cKDTree(pv)
for r in ratios:
    # per-face source label of the output: -1 kept/protected, 0 free part, g for each group, -2 protected at a ratio
    labels = [0] + list(gsel) + ([-2] if PROT_RATIO < 1 else [])
    parts = [decimate(f'{tmp}/in.obj', max(int(len(faces) * r) - int(round(prot.sum() * PROT_RATIO)) - int(kept.sum())
                                           - gbudget, 200))]
    parts += [decimate(f'{tmp}/group{g}.obj', int(len(sel) * gratios[g])) for g, sel in gsel.items()]
    if PROT_RATIO < 1:
        parts.append(decimate(f'{tmp}/prot.obj', int(prot.sum() * PROT_RATIO)))
    # weld back: kept protected faces use their original vertices; decimated vertices that coincide with an original
    # cut-edge vertex reuse it
    whole = kept if PROT_RATIO < 1 else kept | prot
    allv, newf, neww, welded = [d['verts']], [faces[whole]], [wuv[whole].reshape(-1, 2)], 0
    group = [np.full(int(whole.sum()), -1)] + [np.full(len(f), g) for (_, f, _), g in zip(parts, labels)]
    off = len(d['verts'])
    for v, f, w in parts:
        dist, nearest = tree.query(v)
        vid = np.where(dist < 1e-7, nearest, off + np.arange(len(v)))
        allv.append(v); newf.append(vid[f]); neww.append(w); off += len(v); welded += int((dist < 1e-7).sum())
    allv, newf, neww = np.concatenate(allv), np.concatenate(newf), np.concatenate(neww)
    keep = np.unique(newf); m2 = -np.ones(len(allv), int); m2[keep] = np.arange(len(keep))
    np.savez(f'{work}/mesh_r{int(r * 100)}.npz', verts=allv[keep], faces=m2[newf], wuv=neww, group=np.concatenate(group),
             src_index=np.where(keep < len(d['verts']), keep, -1))
    print('DECIMATED', r, len(newf), 'faces (', int(prot.sum()), 'protected at', PROT_RATIO, ';', int(kept.sum()), 'kept;', welded, 'welded )')
