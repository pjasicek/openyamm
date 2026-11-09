"""Per-piece error sweep: every decimation group of work/groups.npy alone at ratios 0.9 .. 0.3, with and without the
volume-restoring inflation (decimate_pieces.inflate), checked (closed stays closed, no new self-intersections, no face
turned over against the source) and measured at rest: two-way point-to-surface distance (pymeshlab Hausdorff, faces
and vertices sampled), max and mean, in mm, and the growth of the rest gap to each neighbouring piece. Writes work/sweep.json {group: [[ratio, inflate, faces, max, mean, ok, volume, gap growth]]}.
Usage: sweep_groups.py"""
import json, os, sys
import numpy as np
import pymeshlab as ml
sys.argv = [sys.argv[0], 'work', '1.0']
os.environ['SWEEP_IMPORT'] = '1'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import decimate_pieces as D  # noqa: E402  (module import writes the group OBJs and returns before the ladder loop)

RATIOS = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
# joint contacts: the first f80 opened 5.8 mm at both index-finger knuckles in the bind pose (detached-parts audit): the
# reduced middle phalanx pulled its end back from the proximal one. Each row also records the worst growth (mm) of the rest
# gap between the piece and every source piece within NEAR of it (the dagger and the kept pieces included)
NEAR = 0.005
SEARCH = float(os.environ.get('GAP_SEARCH', '0.005'))
from scipy.spatial import cKDTree  # noqa: E402
_, F_, _, COMP, _ = __import__('pieces').pieces(os.path.join(HERE, 'work'))
VT = cKDTree(D.pv)


def neighbours(sel):
    own = set(np.unique(COMP[sel]).tolist()); vs = np.unique(D.faces[sel])
    hits = VT.query_ball_point(D.pv[vs], SEARCH)   # skelwar: candidates by vertices within 3 cm (large faces), kept if the gap < NEAR
    near = {int(v) for h in hits for v in h}
    fv = np.zeros(len(D.pv), bool); fv[list(near)] = True
    out = {}
    for k in np.unique(COMP[fv[D.faces].any(1)]):
        if int(k) in own:
            continue
        out[int(k)] = np.where(COMP == k)[0]
    sf = D.faces[sel]
    return {k: v for k, v in out.items() if gap(D.pv, sf, v) < NEAR * 1000} if SEARCH > NEAR else out


def gap(v, f, nf):
    ms = ml.MeshSet(); ms.add_mesh(mesh(v, f)); ms.add_mesh(mesh(D.pv, D.faces[nf]))
    return ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=4000)['min'] * 1000


def mesh(v, f):
    u, inv = np.unique(f, return_inverse=True)
    return ml.Mesh(v[u], inv.reshape(-1, 3).astype(np.int32))


def two_way(sv, sf, cv, cf):
    ms = ml.MeshSet(); ms.add_mesh(mesh(sv, sf)); ms.add_mesh(mesh(cv, cf))
    a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=3000)
    b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=3000)
    return max(a['max'], b['max']) * 1000, max(a['mean'], b['mean']) * 1000


out = {}
for g, sel in D.sel_of.items():
    base, cat, n = D.plan[g]
    sf = D.faces[sel]; so, sn = D.open_edges(sf); svol = D.volume(D.pv, sf)
    nb = neighbours(sel); g0 = {k: gap(D.pv, sf, nf) for k, nf in nb.items()}
    rows = []
    for r in RATIOS:
        target = max(D.MIN_FACES, int(round(len(sel) * r)))
        if target >= len(sel):
            continue
        v0, f, w, nsi0 = D.decimate(g, target)
        for infl in ((0, 1) if so == 0 else (0,)):
            v, nsi = v0, nsi0
            if infl:
                v, dd = D.inflate(v0, f, svol); nsi = D.selfx(v, f)
            o, nm = D.open_edges(f); fl = D.flipped(v, f, D.pv, sf)
            vol = D.volume(v, f) / svol if so == 0 else 1.0
            ok = bool(o <= so and nm <= sn and nsi <= D.src_si[g] and fl == 0 and (so > 0 or 0.8 < vol < 1.2))
            mx, mean = two_way(D.pv, sf, v, f)
            dg = max([gap(v, f, nf) - g0[k] for k, nf in nb.items()] or [0.0])
            rows.append([r, infl, int(len(f)), round(mx, 2), round(mean, 3), ok, round(vol, 3), round(dg, 2)])
    out[g] = dict(cat=cat, n=int(n), rows=rows)
    best = [x for x in rows if x[5]]
    print(f'g{g:3d} {cat:6s} {n:4d}', ' '.join(f'{x[0]:.1f}{"i" if x[1] else ""}:{x[3]:.1f}/{x[4]:.2f}g{x[7]:.1f}{"" if x[5] else "X"}' for x in rows), flush=True)
json.dump(out, open(os.path.join(HERE, 'work', os.environ.get('SWEEP_OUT', 'sweep.json')), 'w'))
