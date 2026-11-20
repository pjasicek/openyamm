#!/usr/bin/env python3
"""Keep the LOD0 right hand (club grip) and both feet (sole contacts) in every LOD, as the production LOD chain does
(mm8_m440_claude/scripts/preserve_lod_contacts.py, written for the combined body + club file; this is the body-only
version for the reduced export): in each LOD the connected pieces mostly weighted to the right hand/fingers or the
feet/toes are replaced by the LOD0 pieces; the shadow LODs are rebuilt from the colour LODs. Writes
review/lod_contacts.json. Usage: preserve_contacts.py <in.glb> <out.glb>"""
from pathlib import Path
import json, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from merge_head_material import read_glb, write_glb, accessor_array, append_accessor, compact, TYPES  # noqa: E402
from build_actor_lods import merge_shadow  # noqa: E402
D, B = read_glb(Path(sys.argv[1])); B = bytearray(B)
node = next(n for n in D['nodes'] if n.get('name') == 'M440'); base = D['meshes'][node['mesh']]; skin = D['skins'][node['skin']]
names = [D['nodes'][i]['name'] for i in skin['joints']]
protected = np.array([n.startswith(('B_R_Finger', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe', 'B_R_Toe')) for n in names])


def read(pr):
    return {n: accessor_array(D, B, a).copy() for n, a in pr['attributes'].items()}, accessor_array(D, B, pr['indices']).reshape(-1, 3).copy()


def selected(v, t):
    _, w = np.unique(np.round(v['POSITION'], 6), axis=0, return_inverse=True); w = w.ravel()
    e = w[t[:, [0, 1, 1, 2, 2, 0]]].reshape(-1, 2); n = w.max() + 1
    _, labels = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    labels = labels[w]; face = labels[t[:, 0]]
    weights = (protected[v['JOINTS_0']] * v['WEIGHTS_0']).sum(1)
    return np.isin(face, np.unique(labels[weights > .5]))


refs = {}
for pr in base['primitives']:
    v, t = read(pr); take = selected(v, t)
    if take.any():
        refs[pr['material']] = (v, t[take])
report = []
for mi in base['extras']['openyamm_lods']:
    for pr in D['meshes'][mi]['primitives']:
        if pr['material'] not in refs:
            continue
        v, t = read(pr); take = selected(v, t); rv, rt = refs[pr['material']]
        used, indices = np.unique(t[~take].ravel(), return_inverse=True); rused, rindices = np.unique(rt.ravel(), return_inverse=True)
        for name, old in list(pr['attributes'].items()):
            a = D['accessors'][old]; values = np.concatenate([v[name][used], rv[name][rused]]).astype(TYPES[a['componentType']])
            pr['attributes'][name] = append_accessor(D, B, values, a, 34962)
        ind = np.concatenate([indices, rindices + len(used)]).astype(np.uint32)
        assert len(ind) % 3 == 0 and len(ind) // 3 == len(t) - int(take.sum()) + len(rt)
        pr['indices'] = append_accessor(D, B, ind, {'type': 'SCALAR', 'componentType': 5125}, 34963)
        report.append({'mesh': D['meshes'][mi]['name'], 'removed_triangles': int(take.sum()), 'retained_contact_triangles': len(rt)})
for mi, si in zip([node['mesh']] + base['extras']['openyamm_lods'], base['extras']['openyamm_shadow_lods']):
    D['meshes'][si] = merge_shadow(D, B, D['meshes'][mi])
counts = [sum(D['accessors'][q['indices']]['count'] // 3 for q in D['meshes'][mi]['primitives']) for mi in [node['mesh']] + base['extras']['openyamm_lods']]
assert all(a > b for a, b in zip(counts, counts[1:]))
write_glb(Path(sys.argv[2]), *compact(D, B))
(P / 'review/lod_contacts.json').write_text(json.dumps({'triangles': counts, 'repairs': report}, indent=2) + '\n')
print('CONTACT_PRESERVING_LODS', counts)
