"""Mirror-symmetric texture-aware quadric decimation (MeshLab) of the Winged Mutant (from decimate_tex.py of the
dwarf/m492 reduce projects). The installed model is exactly symmetric about x = 0 (both halves share texels; the user
asked for that symmetry in the rework), so only the +x half is decimated and the result is mirrored:
- inputs work/mesh_in.npz and work/sets.npz (make_sets.py): side, wing back copies, exact keep set, groups;
- each group of +x faces (0 body at the ladder ratio, the rest at REA_GROUP_RATIOS, e.g. 1:0.7,2:0.55,3:0.8) is cut out
  and decimated on its own with its cut edge, the symmetry plane and the open wing/hair borders preserved (MeshLab
  preserveboundary: boundary vertices stay put), then welded back to the kept faces;
- the wing back copies are not decimated: they are rebuilt from the reduced front sheet as the creature's
  add_backfaces.py made them (same UVs and weights, winding flipped, 2 mm behind along the vertex normal); a back
  vertex whose front vertex is an unchanged source vertex takes that vertex's source back twin exactly;
- the -x half is the mirror of the +x half (positions x -> -x, winding reversed, same UVs), its source vertices
  mapped to their source mirror twins, plane vertices shared.
Usage: decimate_sym.py <work dir> <ratio,...> -> work/mesh_r<NN>.npz (verts, faces, wuv, group, src_index, back)"""
import os
import struct
import sys
import zlib
import numpy as np
import pymeshlab as ml
from scipy.spatial import cKDTree

work, ratios = sys.argv[1], [float(r) for r in sys.argv[2].split(',')]
d = np.load(f'{work}/mesh_in.npz'); S = np.load(f'{work}/sets.npz')
OFFSET = 0.002
tmp = f'{work}/obj'; os.makedirs(tmp, exist_ok=True)
chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
open(f'{tmp}/tex.png', 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
                                    + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
open(f'{tmp}/in.mtl', 'w').write('newmtl m\nmap_Kd tex.png\n')
V, F = d['verts'], d['faces']; WUV = d['wuv'].reshape(-1, 3, 2)
side, back, keep, groups = S['side'], S['back'], S['keep'], S['group']
# a group ratio may follow the ladder ratio: '1:r', '2:r*0.8', '3:min(1,r+0.1)'
gratios = {int(k): x for k, x in (kv.split(':') for kv in os.environ.get('REA_GROUP_RATIOS', '').split(',') if kv)}
half = side == 1

# source mirror twins (exact symmetry: every vertex has one; plane vertices are their own)
mtree = cKDTree(V)
dm, mirror = mtree.query(V * [-1, 1, 1])
assert dm.max() < 3e-5, dm.max(); assert (mirror[mirror] == np.arange(len(V))).all()
# source wing back twins: back face corners are the front face's corners reversed, offset 2 mm
back_twin = -np.ones(len(V), int)
fo = S['front_of']
for b in np.where(back)[0]:
    a = fo[b]; fa, fb = F[a], F[b]
    for i in range(3):   # match corners by UV
        j = int(np.argmin(np.linalg.norm(WUV[b] - WUV[a][i], axis=1)))
        back_twin[fa[i]] = fb[j]
src_front = (S['group'] == 2) & ~back
# mirror UVs: body and wing halves share texels, but the head set (HeadUV re-laid by uv_atlas over the whole head) has
# its own charts per side, so a mirrored wedge takes the UV of the mirror source face at the same barycentric point
fkey = {tuple(sorted(t)): i for i, t in enumerate(F.tolist())}
mface = np.array([fkey[tuple(sorted(mirror[t].tolist()))] for t in F])
mcorner = np.array([[list(F[mface[i]]).index(mirror[F[i][k]]) for k in range(3)] for i in range(len(F))])
MUV = np.take_along_axis(WUV[mface], mcorner[:, :, None], 1)   # per source face/corner: the mirror face's UV there
plus_f = np.where(side == 1)[0]
uvtree = cKDTree(WUV[plus_f].mean(1))


# UV islands of the +x head faces (faces joined across edges whose two ends carry the same UVs)
_par = {int(i): int(i) for i in plus_f}
def _find(i):
    while _par[i] != i:
        _par[i] = _par[_par[i]]; i = _par[i]
    return i
_edges = {}
for i in plus_f:
    for k in range(3):
        a_, b_ = F[i][k], F[i][(k + 1) % 3]; ua, ub = tuple(np.round(WUV[i][k], 6)), tuple(np.round(WUV[i][(k + 1) % 3], 6))
        key = (a_, ua, b_, ub) if a_ < b_ else (b_, ub, a_, ua)
        if key in _edges:
            x, y = _find(int(i)), _find(_edges[key])
            if x != y:
                _par[x] = y
        else:
            _edges[key] = int(i)
island = {i: _find(i) for i in _par}


def _bary(t, uv):
    a, b, c = WUV[t]; m = np.array([b - a, c - a]).T
    l1, l2 = np.linalg.solve(m, uv - a)
    return np.array([1 - l1 - l2, l1, l2])


def mirror_face_uv(uvs):
    """Mirror-side UVs of a new +x face's three wedges: the +x source triangle containing (or nearest to) the face's UV
    centroid fixes the island; each wedge maps through the island triangle that contains it (barycentric onto the
    mirror face's corner UVs), or through the centroid triangle's affine map when it lies outside the island. Wedges
    mapped one by one could land in different islands (gutters) and span the -x atlas (q82 first export: -x head UV
    area 5x the +x one)."""
    cen = uvs.mean(0)
    _, cand = uvtree.query(cen, 32); cand = plus_f[cand]
    best = None
    for t in cand:
        try:
            br = _bary(t, cen)
        except np.linalg.LinAlgError:
            continue
        out = -min(br.min(), 0)
        if best is None or out < best[0]:
            best = (out, t)
        if out == 0:
            break
    t0 = best[1]; isl = island[int(t0)]; res = np.zeros((3, 2)); outside = 0
    for k in range(3):
        _, cand = uvtree.query(uvs[k], 32); hit = None
        for t in plus_f[cand]:
            if island[int(t)] != isl:
                continue
            try:
                br = _bary(t, uvs[k])
            except np.linalg.LinAlgError:
                continue
            if br.min() >= -1e-6:
                hit = (t, br); break
        if hit is None:
            hit = (t0, _bary(t0, uvs[k])); outside += 1
        res[k] = hit[1] @ MUV[hit[0]]
    return res, outside


def write_obj(path, sel):
    used = np.unique(F[sel]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x} {y} {z}\n' for x, y, z in V[used])
        f.writelines(f'vt {u} {v}\n' for u, v in WUV[sel].reshape(-1, 2))
        f.write('usemtl m\n')
        f.writelines(f'f {remap[a]+1}/{3*i+1} {remap[b]+1}/{3*i+2} {remap[c]+1}/{3*i+3}\n'
                     for i, (a, b, c) in enumerate(F[sel]))


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
    return np.array(vs), np.array(fs, np.int32), np.array(vts)[np.array(fts).reshape(-1)].reshape(-1, 3, 2)


def decimate(obj, target):
    ms = ml.MeshSet(); ms.load_new_mesh(obj)
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=.3, extratcoordw=1.0,
        preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.save_current_mesh(f'{tmp}/out.obj', save_textures=False)
    return read_obj(f'{tmp}/out.obj')


# NOMIRROR groups (default 1, the hair) are decimated on both sides as they are, not mirrored: the head set's charts are
# cut differently per side (51 of 169 +x islands have no affine map onto the -x layout), so a mirrored hair wedge cannot
# take a -x UV (q82's first export spread 96 -x hair faces across the head atlas)
NOMIRROR = {int(x) for x in os.environ.get('NOMIRROR', '1').split(',') if x}
sel_g = {}
for g in sorted(set(groups[(side != 0) & ~keep & ~back])):
    region = (side != 0) if g in NOMIRROR else half
    sel_g[g] = np.where(region & ~keep & ~back & (groups == g))[0]
    write_obj(f'{tmp}/g{g}.obj', sel_g[g])
kept_h = np.where(half & keep & ~back)[0]
plane_f = np.where(side == 0)[0]


def vnormals(v, f):
    n = np.zeros_like(v); fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


for r in ratios:
    # +x half: kept faces on source vertices, decimated groups welded to source vertices where they coincide
    allv, faces, wuv, lab = [V], [F[kept_h]], [WUV[kept_h]], [np.full(len(kept_h), -1)]
    off = len(V)
    for g, sel in sel_g.items():
        ratio = float(eval(gratios.get(g, 'r' if g == 0 else '1.0'), {'min': min, 'max': max}, {'r': r}))
        if ratio >= 1:
            faces.append(F[sel]); wuv.append(WUV[sel]); lab.append(np.full(len(sel), g)); continue
        nv, nf, nw = decimate(f'{tmp}/g{g}.obj', max(int(len(sel) * ratio), 8))
        dist, nearest = mtree.query(nv)
        vid = np.where(dist < 1e-7, nearest, off + np.arange(len(nv)))
        allv.append(nv); faces.append(vid[nf]); wuv.append(nw); lab.append(np.full(len(nf), g)); off += len(nv)
    allv = np.concatenate(allv); faces = np.concatenate(faces); wuv = np.concatenate(wuv); lab = np.concatenate(lab)
    nsrc = len(V)
    # wing back copies for the front membrane faces (source faces that had one; new faces of the wing group)
    # as add_backfaces.py: edge-connected components of the wing-material faces; a component with an open edge
    # (open in the whole front mesh) gets a back copy
    from collections import defaultdict
    wingf = np.where(wuv[:, 0, 0] // 2 == 1)[0]
    ecount = defaultdict(int); eface = defaultdict(list)
    for i, t in enumerate(faces):
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (min(e), max(e)); ecount[k] += 1
    wset = set(wingf.tolist())
    for i in wingf:
        t = faces[i]
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            eface[(min(e), max(e))].append(i)
    parent = {i: i for i in wingf}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for fs in eface.values():
        for j in fs[1:]:
            a, b = find(fs[0]), find(j)
            if a != b:
                parent[a] = b
    openroot = {find(fs[0]) for k, fs in eface.items() if ecount[k] == 1}
    needs = np.zeros(len(faces), bool)
    needs[[i for i in wingf if find(i) in openroot]] = True
    bf = faces[needs]
    used = np.unique(bf)
    # front-sheet vertex normals from the reduced membrane faces only (as the creature's back-face offset)
    nrm = vnormals(allv, faces[(wuv[:, 0, 0] // 2 == 1)])
    bmap = {}
    newv = []
    for vi in used:
        if vi < nsrc and back_twin[vi] >= 0:
            bmap[vi] = back_twin[vi]
        else:
            bmap[vi] = off + len(newv); newv.append(allv[vi] - nrm[vi] * OFFSET)
    if newv:
        allv = np.concatenate([allv, np.array(newv)]); off += len(newv)
    bfaces = np.array([[bmap[a] for a in t] for t in bf])[:, ::-1]
    bwuv = wuv[needs][:, ::-1]
    faces = np.concatenate([faces, bfaces]); wuv = np.concatenate([wuv, bwuv]); lab = np.concatenate([lab, np.full(len(bfaces), 5)])
    isback = np.r_[np.zeros(len(faces) - len(bfaces), bool), np.ones(len(bfaces), bool)]
    # mirror the half: source vertices -> source twins, new vertices -> new mirrored copies, plane vertices shared
    nh = len(allv)
    mmap = np.empty(nh, int); mmap[:nsrc] = mirror
    newidx = np.arange(nsrc, nh)
    mmap[nsrc:] = nh + np.arange(len(newidx))
    allv = np.concatenate([allv, allv[nsrc:] * [-1, 1, 1]])
    own = np.isin(lab, list(NOMIRROR))          # both-sided groups: keep as they are, no mirror copy
    mfaces, mlab, mwuv = faces[~own], lab[~own], wuv[~own]
    mf = mmap[mfaces][:, ::-1]
    # mirrored wedge UVs: source faces take their mirror face's UVs exactly, new wedges are mapped (mirror_uv)
    sfk = {tuple(sorted(t)): i for i, t in enumerate(F[plus_f].tolist())}
    mw = np.empty_like(mwuv); mapped, worst = 0, 0
    for i, t in enumerate(mfaces):
        j = sfk.get(tuple(sorted(t.tolist()))) if (t < nsrc).all() else None
        if j is not None:
            mw[i] = [MUV[plus_f[j]][list(F[plus_f[j]]).index(t[k])] for k in range(3)]
        elif (mwuv[i, 0, 0] // 2) != 2:
            mw[i] = mwuv[i]   # body and wing: shared texels
        else:
            mw[i], o = mirror_face_uv(mwuv[i]); mapped += 1; worst += o
    mw = mw[:, ::-1]
    print('MIRROR UV mapped', mapped, 'new head faces;', worst, 'wedges outside their island (affine extrapolation)')
    faces = np.concatenate([faces, mf, F[plane_f]]); wuv = np.concatenate([wuv, mw, WUV[plane_f]])
    lab = np.concatenate([lab, mlab, np.full(len(plane_f), -1)]); isback = np.r_[isback, isback[~own], np.zeros(len(plane_f), bool)]
    keepv = np.unique(faces); m2 = -np.ones(len(allv), int); m2[keepv] = np.arange(len(keepv))
    np.savez(f"{os.environ.get('OUTDIR', work)}/mesh_r{int(round(r * 100))}.npz", verts=allv[keepv], faces=m2[faces], wuv=wuv.reshape(-1, 2), group=lab,
             back=isback, src_index=np.where(keepv < nsrc, keepv, -1))
    cnt = {int(g): int((lab == g).sum()) for g in np.unique(lab)}
    print('DECIMATED', r, len(faces), 'faces; per label', cnt, 'new back verts', len(newv), 'per side')
