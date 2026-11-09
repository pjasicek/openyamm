"""Digits (fingers, toes) of a mesh by connectivity: a geodesic distance from the wrist/ankle ring gives a merge tree;
a digit is a leaf branch of it (the earliest component that never splits again). Each digit's centreline comes from
level-set ring centres. Joints go at MM9's phalanx fractions along it."""
import heapq
import itertools
import numpy as np


def geodesic(P, nbr, seeds, allow):
    d = np.full(len(P), np.inf)
    pq = []
    for s in seeds:
        d[s] = 0; pq.append((0.0, int(s)))
    heapq.heapify(pq)
    while pq:
        di, i = heapq.heappop(pq)
        if di > d[i]:
            continue
        for j in nbr[i]:
            if not allow[j]:
                continue
            nd = di + np.linalg.norm(P[i] - P[j])
            if nd < d[j]:
                d[j] = nd; heapq.heappush(pq, (nd, j))
    return d


def branches(d, nbr, ids, min_len, min_verts):
    """Process vertices from far to near; union-find; when two live components merge, each with enough length is a
    finished branch."""
    order = ids[np.argsort(-d[ids])]
    par = {}
    info = {}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    done = []
    for v in order:
        par[v] = v
        info[v] = {'verts': [int(v)], 'tip': float(d[v]), 'tipv': int(v)}
        roots = {find(n) for n in nbr[v] if n in par and n != v}
        for r in roots:
            a, b = find(v), r
            if a == b:
                continue
            ia, ib = info[a], info[b]
            big = lambda i: (i['tip'] - d[v]) >= min_len and len(i['verts']) >= min_verts
            if big(ia) and big(ib):
                done.append(dict(ia, base=float(d[v])))
                done.append(dict(ib, base=float(d[v])))
                # the merged thing continues from v only: both finished branches are cut off
                par[a] = a; par[b] = b
                new = v if a != v else v
                info[a] = {'verts': [int(v)], 'tip': float(d[v]), 'tipv': int(v)}
                par[b] = a
                continue
            if len(ia['verts']) < len(ib['verts']):
                a, b, ia, ib = b, a, ib, ia
            par[b] = a
            ia['verts'] += ib['verts']
            if ib['tip'] > ia['tip']:
                ia['tip'], ia['tipv'] = ib['tip'], ib['tipv']
    return done


def centreline(P, d, verts, n, base):
    verts = np.array(verts)
    lo, hi = d[verts].min(), d[verts].max()
    t = np.linspace(lo, hi, n + 1)
    C = []
    for a, b in zip(t[:-1], t[1:]):
        m = verts[(d[verts] >= a) & (d[verts] <= b)]
        if len(m):
            C.append(0.5 * (P[m].min(0) + P[m].max(0)))
    C[-1] = P[verts[np.argmax(d[verts])]]
    return np.array(C)


def along(C, f):
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    x = f * L[-1]
    i = min(int(np.searchsorted(L, x)), len(C) - 1)
    if i == 0:
        return C[0]
    w = (x - L[i - 1]) / max(L[i] - L[i - 1], 1e-9)
    return C[i - 1] * (1 - w) + C[i] * w


def find_digits(P, nbr, cfg, newJ, J):
    joints, report, labels = {}, {}, {}
    for spec in cfg:
        root = newJ[spec['root']]
        sx = np.sign(root[0])
        region = np.linalg.norm(P - root, axis=1) < spec['radius']
        region &= (np.sign(P[:, 0]) == sx)
        fw = root - newJ[spec['parent']]
        region &= (P - root) @ (fw / np.linalg.norm(fw)) > spec.get('behind', -0.012)
        seeds = [i for i in np.nonzero(region)[0] if np.linalg.norm(P[i] - root) < spec['seed']]
        d = geodesic(P, nbr, seeds, region)
        ids = np.nonzero(np.isfinite(d))[0]
        br = branches(d, nbr, ids, spec['min_len'], spec['min_verts'])
        br.sort(key=lambda b: -(b['tip'] - b['base']))
        br = br[:spec['count']]
        rep = [{'tip': P[b['tipv']].round(3).tolist(), 'len': round(b['tip'] - b['base'], 3), 'verts': len(b['verts'])} for b in br]
        names = spec['chains']
        # MM9 digit directions from the wrist; assign by the best permutation of the direction match
        mdir = []
        for ch in names:
            v = J[ch[-1]] - J[spec['root']]
            mdir.append(v / np.linalg.norm(v))
        odir = []
        for b in br:
            v = P[b['tipv']] - root
            odir.append(v / np.linalg.norm(v))
        best, bs = None, -1e9
        for perm in itertools.permutations(range(len(br)), min(len(names), len(br))):
            sc = sum(float(mdir[k] @ odir[bi]) for k, bi in enumerate(perm))
            if sc > bs:
                best, bs = perm, sc
        for k, bi in enumerate(best):
            b = br[bi]
            ch = names[k]
            C = centreline(P, d, b['verts'], 10, b['base'])
            Lt = spec.get('digit_len', {}).get(ch[0])
            if Lt:                      # keep the last Lt of the centreline: knuckles level across a fused palm
                LL = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
                if LL[-1] > Lt:
                    st = along(C, 1 - Lt / LL[-1])
                    C = np.vstack([st, C[LL > LL[-1] - Lt]])
                else:
                    ext = (C[0] - C[1]) / np.linalg.norm(C[0] - C[1]) * (Lt - LL[-1])
                    C = np.vstack([C[0] + ext, C])
            mm = [J[n] for n in ch]
            seg = [np.linalg.norm(mm[i + 1] - mm[i]) for i in range(len(mm) - 1)]
            seg.append(seg[-1] * spec.get('tip_share', 1.0))
            fr = np.r_[0, np.cumsum(seg)] / sum(seg)
            for n, f in zip(ch, fr[:-1]):
                joints[n] = along(C, f)
            labels['|'.join(ch)] = np.array(b['verts'])
            rep[bi]['chain'] = ch[0]
        report[spec['root']] = rep
    return {'joints': joints, 'report': report, 'labels': labels}
