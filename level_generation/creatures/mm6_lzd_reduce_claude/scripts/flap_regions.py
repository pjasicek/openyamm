#!/usr/bin/env python3
"""Loin-flap vertex lists per LOD for the shared gate config (lod_regions.<colourN|shadowN>.flap_geometry): every
vertex of the connected pieces (shared indices, positions welded) of each decoded LOD mesh (primitives concatenated)
that contain a vertex with LoinFlap weight >= 0.5 (reproduces the Codex lists on the installed model). Usage: flap_regions.py <glb>
[config.json to update in place]"""
import json, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
doc, b = read_glb(Path(sys.argv[1]))
node = next(n for n in doc['nodes'] if n.get('name') == 'Lizard')
joints = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]; flap = joints.index('LoinFlap')
mesh = doc['meshes'][node['mesh']]; ex = mesh['extras']


def arr(i):
    a = doc['accessors'][i]; k = {'VEC4': 4}[a['type']]
    code = {5121: 'B', 5123: 'H', 5126: 'f'}[a['componentType']]
    v = np.array(struct.unpack(f'<{a["count"] * k}{code}', accessor_bytes(doc, b, i)), float).reshape(-1, 4)
    return v / 255 if a.get('normalized') and code == 'B' else v / 65535 if a.get('normalized') and code == 'H' else v


def flap_vertices(m):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    out, off = [], 0
    for p in m['primitives']:
        at = p['attributes']; n = doc['accessors'][at['POSITION']]['count']; w = np.zeros(n)
        for s in ('0', '1'):
            if 'JOINTS_' + s in at:
                j, wt = arr(at['JOINTS_' + s]), arr(at['WEIGHTS_' + s]); w += (wt * (j == flap)).sum(1)
        ia = doc['accessors'][p['indices']]; code = {5121: 'B', 5123: 'H', 5125: 'I'}[ia['componentType']]
        f = np.array(struct.unpack(f'<{ia["count"]}{code}', accessor_bytes(doc, b, p['indices']))).reshape(-1, 3)
        pos = np.array(struct.unpack(f'<{n * 3}f', accessor_bytes(doc, b, at['POSITION']))).reshape(-1, 3)
        _, weld = np.unique(np.round(pos, 6), axis=0, return_inverse=True); weld = weld.reshape(-1)
        r = np.r_[f[:, 0], f[:, 1], f[:, 2], np.arange(n)]; c = np.r_[f[:, 1], f[:, 2], f[:, 0], n + weld]
        lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n + weld.max() + 1,) * 2), directed=False)[1][:n]
        hit = np.unique(lab[w >= .5])
        out += [int(i) + off for i in np.where(np.isin(lab, hit))[0]]; off += n
    return out


regions = {}
for k, mi in enumerate([node['mesh']] + ex['openyamm_lods']):
    regions[f'colour{k}'] = {'flap_geometry': {'vertices': flap_vertices(doc['meshes'][mi])}}
for k, mi in enumerate(ex['openyamm_shadow_lods']):
    regions[f'shadow{k}'] = {'flap_geometry': {'vertices': flap_vertices(doc['meshes'][mi])}}
print({k: len(v['flap_geometry']['vertices']) for k, v in regions.items()})
if len(sys.argv) > 2:
    c = json.load(open(sys.argv[2])); c['lod_regions'] = regions; json.dump(c, open(sys.argv[2], 'w'), indent=1)
else:
    print(json.dumps(regions)[:300])
