"""(Copied from ../mm9_skeleton_reduce_claude; skelwar: lined groups by face flag.) Texture-aware quadric decimation (MeshLab) of the skeleton, one bone piece at a time (decimate_tex.py of the
reduce projects, reorganised for separate rigid pieces). The pooled collapse of the reference projects eats the small
pieces first (their absolute error is tiny): here every piece is its own group (make_groups.py) with its own target,
so a phalanx keeps its share and a femur takes a strong cut.
Each group is written to OBJ with wedge UVs (material in u + 2 * mat), decimated alone (boundary kept: the cranium dome
meets the kept skull face; the vest/strap sheets keep their hems), and checked: a closed piece must stay closed, no
piece may self-intersect, no piece may lose its volume (signed volume within 70-130 % of the source piece), and no
face may turn over against its source neighbourhood. A failing piece is retried 0.1 higher, up to kept exactly.
Group faces that touch kept faces weld back by exact positions (boundary vertices stay put).
Usage: decimate_pieces.py <work dir> <NN=plan.json,...>  (plan: {group: [ratio, category, faces, inflate]} from
plan_from_sweep.py; target per group = round(faces * ratio)) -> work/mesh_r<NN>.npz (verts, faces, wedge uv, group,
src_index, sheet flag per face for the lining rebuild)"""
import json
import os
import struct
import sys
import zlib
import numpy as np
import pymeshlab as ml
from scipy.spatial import cKDTree

work = sys.argv[1]
scales = [kv.split('=') for kv in sys.argv[2].split(',')] if '=' in sys.argv[2] else []
d = np.load(f'{work}/mesh_in.npz')
groups = np.load(os.environ.get('REA_GROUPS', f'{work}/groups.npy'))
plan = {int(k): v for k, v in json.load(open(os.environ.get('REA_PLAN', f'{work}/group_plan.json'))).items()}
MIN_FACES = int(os.environ.get('MIN_FACES', '16'))
# texture weight of the collapse (brief 2026-11-04, Trellborg: 3-8 halved the smeared painted bands at the same count)
TEXW = float(os.environ.get('TEXW', '1.0'))
tmp = f'{work}/obj'; os.makedirs(tmp, exist_ok=True)
chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
open(f'{tmp}/tex.png', 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
                                    + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
open(f'{tmp}/in.mtl', 'w').write('newmtl m\nmap_Kd tex.png\n')
faces, wuv = d['faces'], d['wuv'].reshape(-1, 3, 2)
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
    used = np.unique(faces[sel]); remap = -np.ones(len(pv), int); remap[used] = np.arange(len(used))
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x!r} {y!r} {z!r}\n' for x, y, z in pv[used].tolist())
        f.writelines(f'vt {u!r} {v!r}\n' for u, v in wuv[sel].reshape(-1, 2).tolist())
        f.write('usemtl m\n')
        f.writelines(f'f {remap[a]+1}/{3*i+1} {remap[b]+1}/{3*i+2} {remap[c]+1}/{3*i+3}\n'
                     for i, (a, b, c) in enumerate(faces[sel]))


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
    return np.array(vs), np.array(fs, np.int64), np.array(vts)[np.array(fts).reshape(-1)]


def open_edges(f):
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1)
    _, c = np.unique(e, axis=0, return_counts=True)
    return int((c == 1).sum()), int((c > 2).sum())


def volume(v, f):
    return float(np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6)


FOLD_COS = float(os.environ.get('FOLD_COS', '-0.17'))


def flipped(v, f, sv, sf):
    """faces whose normal points against the normal of the nearest source face (> 100 deg; skelwar config c: FOLD_COS=0.34,
    > 70 deg, also catches folds: b95 stood a 2 x 8 cm face upright on a back skirt plate, normal 90 deg off the plate)"""
    sn = np.cross(sv[sf[:, 1]] - sv[sf[:, 0]], sv[sf[:, 2]] - sv[sf[:, 0]])
    sn /= np.linalg.norm(sn, axis=1, keepdims=True) + 1e-20
    n = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-20
    _, nn = cKDTree(sv[sf].mean(1)).query(v[f].mean(1), 3)
    return int(((sn[nn] * n[:, None]).sum(-1).max(1) < FOLD_COS).sum())


DMAX = float(os.environ.get('INFLATE_MAX', '0.004'))
VOL_LO, VOL_HI = float(os.environ.get('VOL_LO', '0.8')), float(os.environ.get('VOL_HI', '1.2'))


def inflate(v, f, svol):
    """A collapsed thin piece (rib, phalanx, femur shaft) loses cross-section: its facets cut chords through the round
    source. Push the vertices out along their normals by one offset that gives the source volume back (capped at
    DMAX); the facets then straddle the source surface instead of lying inside it."""
    vol = volume(v, f)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); area = np.linalg.norm(fn, axis=1).sum() / 2
    dd = float(np.clip((svol - vol) / max(area, 1e-12), 0, DMAX))
    n = np.zeros_like(v)
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-20
    return v + dd * n, dd


def selfx(v, f):
    ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(vertex_matrix=v, face_matrix=f.astype(np.int32)))
    ms.compute_selection_by_self_intersections_per_face()
    return ms.current_mesh().selected_face_number()


def decimate(g, target):
    ms = ml.MeshSet(); ms.load_new_mesh(f'{tmp}/g{g}.obj')
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=.3, extratcoordw=TEXW,
        preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
    ms.compute_selection_by_self_intersections_per_face()
    nsi = ms.current_mesh().selected_face_number()
    ms.save_current_mesh(f'{tmp}/out.obj', save_textures=False)
    v, f, w = read_obj(f'{tmp}/out.obj')
    return v, f, w, nsi


sel_of = {g: np.where(groups == g)[0] for g in plan}
src_si = {}
for g, sel in sel_of.items():
    write_obj(f'{tmp}/g{g}.obj', sel)
    ms = ml.MeshSet(); ms.load_new_mesh(f'{tmp}/g{g}.obj'); ms.compute_selection_by_self_intersections_per_face()
    src_si[g] = ms.current_mesh().selected_face_number()
kept = groups == 0
tree = cKDTree(pv)
sheetf = np.load(f'{work}/sheet_faces.npy')
for tag, pfile in ([] if os.environ.get('SWEEP_IMPORT') else scales):
    gp = {int(k): v for k, v in json.load(open(pfile)).items()}
    parts, labels, log, infl = [], [], [], []
    for g, sel in sel_of.items():
        base, cat, n, use_infl = gp[g]
        s = 1.0
        sv_, sf_ = pv, faces[sel]
        so, sn_ = open_edges(sf_); svol = volume(pv, sf_)
        r = min(1.0, base * s); res = None
        while r < 0.999:
            target = max(MIN_FACES, int(round(len(sel) * r)))
            if target >= len(sel):
                break
            v, f, w, nsi = decimate(g, target)
            dd = 0.0
            if so == 0 and use_infl:
                v, dd = inflate(v, f, svol); nsi = selfx(v, f)
            o, nm = open_edges(f); vol = volume(v, f); fl = flipped(v, f, pv, sf_)
            ok = o <= so and nm <= sn_ and nsi <= src_si[g] and fl == 0 and \
                (so > 0 or VOL_LO < vol / svol < VOL_HI)
            infl.append(dd)
            if ok:
                res = (v, f, w); break
            log.append(f'g{g} {cat} n{n} r{r:.2f}: open {so}->{o} nonman {nm} selfx {src_si[g]}->{nsi} flip {fl} vol {vol / svol if svol else 0:.2f} -> retry')
            r += 0.1
            if r < 0.999:
                log[-1] += f' {r:.2f}'
        if res is None:
            kept_g = sel
            parts.append(None); labels.append(g)
            continue
        parts.append(res); labels.append(g)
    keepf = kept | np.isin(groups, [g for g, p in zip(labels, parts) if p is None])
    allv, newf, neww, glab = [d['verts']], [faces[keepf]], [wuv[keepf].reshape(-1, 2)], [np.zeros(int(keepf.sum()), int)]
    # skelwar: every group whose source faces carry a lining (pauldrons, cuffs, belt, skirt plates, helmet pieces)
    gsheet = {g for g, sel in sel_of.items() if sheetf[sel].any()}
    shl = [sheetf[keepf]]
    off, welded = len(d['verts']), 0
    for p, g in zip(parts, labels):
        if p is None:
            continue
        v, f, w = p
        dist, nearest = tree.query(v)
        vid = np.where(dist < 1e-7, nearest, off + np.arange(len(v)))
        allv.append(v); newf.append(vid[f]); neww.append(w); glab.append(np.full(len(f), g)); off += len(v)
        shl.append(np.full(len(f), g in gsheet))
        welded += int((dist < 1e-7).sum())
    allv, newf, neww, glab = np.concatenate(allv), np.concatenate(newf), np.concatenate(neww), np.concatenate(glab)
    keep = np.unique(newf); m2 = -np.ones(len(allv), int); m2[keep] = np.arange(len(keep))
    np.savez(f'{work}/mesh_r{tag}.npz', verts=allv[keep], faces=m2[newf], wuv=neww, group=glab, sheet=np.concatenate(shl),
             src_index=np.where(keep < len(d['verts']), keep, -1))
    np.save(f'{work}/keep_r{tag}.npy', keepf)
    nkeptg = sum(p is None for p in parts)
    print('DECIMATED', tag, pfile, len(newf), 'faces (', int(kept.sum()), 'kept by plan;', nkeptg, 'groups kept after retries;',
          welded, 'welded )')
    print('  inflation mm: median %.2f p90 %.2f max %.2f' % tuple(np.percentile(np.array(infl) * 1000, [50, 90, 100])))
    for line in log:
        print('  ', line)
