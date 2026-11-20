"""Digits by a level-set merge tree from the wrist: every leaf with a prominence of min_len is one digit, also the last ones that only meet the palm."""
import numpy as np
from digits import geodesic, centreline, along   # noqa


def digit_tree(d, nbr, ids, min_len):
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
        info[v] = {'verts': [int(v)], 'tip': float(d[v]), 'tipv': int(v), 'root': False}
        for n in nbr[v]:
            if n not in par or n == v:
                continue
            a, b = find(v), find(n)
            if a == b:
                continue
            ia, ib = info[a], info[b]
            ba = ia['root'] or ia['tip'] - d[v] >= min_len
            bb = ib['root'] or ib['tip'] - d[v] >= min_len
            if ba and bb:
                for i in (ia, ib):
                    if not i['root']:
                        done.append(dict(i, base=float(d[v])))
                par[b] = a
                info[a] = {'verts': [int(v)], 'tip': float(d[v]), 'tipv': int(v), 'root': True}
                continue
            if ib['root'] or (not ia['root'] and len(ib['verts']) > len(ia['verts'])):
                a, b, ia, ib = b, a, ib, ia
            par[b] = a
            ia['verts'] += ib['verts']
            if ib['tip'] > ia['tip'] and not ia['root']:
                ia['tip'], ia['tipv'] = ib['tip'], ib['tipv']
    return done
