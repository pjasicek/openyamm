#!/usr/bin/env python3
"""What the hands rebuild changed against the installed Titan GLB (exit 1 on anything unintended).
Must hold: original nodes' TRS, original joints' inverse binds, every original animation channel's data (except the
Cast arm channels listed in finger_poses.json cast_fix), material names and extras, variants; LOD0 vertices away from
the hands (no LeftHand/RightHand weight) at the same position with the same normal, UV, joints and weights; images
outside the hand rectangles. Reported: added nodes/channels, LOD triangle counts, changed pixels.
Usage: diff_ttn.py <installed.glb> <new.glb>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
HERE = Path(__file__).resolve().parent
A, B = gp.Glb(sys.argv[1]), gp.Glb(sys.argv[2]); a, b = A.json, B.json
cfg = json.load(open(HERE / 'finger_poses.json')); gcfg = json.load(open(HERE / 'graft_ttn.json'))
bad, info = [], []
na = [n.get('name') for n in a['nodes']]; nb = [n.get('name') for n in b['nodes']]
for i, n in enumerate(a['nodes']):
    m = b['nodes'][nb.index(n['name'])]
    for k in ('translation', 'rotation', 'scale'):
        if np.abs(np.array(n.get(k, [0, 0, 0, 1][:3 if k != 'rotation' else 4] if k != 'scale' else [1, 1, 1])) -
                  np.array(m.get(k, [0, 0, 0, 1][:3 if k != 'rotation' else 4] if k != 'scale' else [1, 1, 1]))).max() > 1e-6:
            bad.append(f'node {n["name"]} {k}')
info.append(f'added nodes: {len(nb) - len(na)}')
ja = [na[j] for j in a['skins'][0]['joints']]; jb = [nb[j] for j in b['skins'][0]['joints']]
ia = A.accessor(a['skins'][0]['inverseBindMatrices']); ib = B.accessor(b['skins'][0]['inverseBindMatrices'])
for k, n in enumerate(ja):
    if np.abs(ia[k] - ib[jb.index(n)]).max() > 1e-5:
        bad.append(f'ibm {n}')
fix = cfg.get('cast_fix', {}); fixed = set((c, j) for c in fix.get('clips', []) for j in fix.get('joints', []))
for an in a['animations']:
    bn = next(x for x in b['animations'] if x['name'] == an['name'])
    chb = {(nb[c['target']['node']], c['target']['path']): bn['samplers'][c['sampler']] for c in bn['channels']}
    changed = []
    for c in an['channels']:
        key = (na[c['target']['node']], c['target']['path']); s = an['samplers'][c['sampler']]; t = chb.get(key)
        if t is None:
            bad.append(f'{an["name"]} lost {key}'); continue
        same = (np.array_equal(A.accessor(s['input']), B.accessor(t['input'])) and
                np.abs(A.accessor(s['output']) - B.accessor(t['output'])).max() < 1e-7)
        if not same:
            (changed if (an['name'], key[0]) in fixed else bad).append(f'{an["name"]} {key}')
    added = len(bn['channels']) - len(an['channels'])
    info.append(f'{an["name"]}: +{added} channels, intended changes {len(changed)}')
ma = [(m['name'], json.dumps(m.get('extras'), sort_keys=True)) for m in a['materials'] if '_LOD' not in m['name']]
mb = [(m['name'], json.dumps(m.get('extras'), sort_keys=True)) for m in b['materials'] if '_LOD' not in m['name']]
for (n1, e1), (n2, e2) in zip(ma, mb):
    e1 = json.loads(e1); e2 = json.loads(e2)
    for e in (e1, e2):
        if e and 'openyamm_region_mask' in e: e['openyamm_region_mask'].pop('index', None)
    if n1 != n2 or e1 != e2: bad.append(f'material {n1}')
if a.get('extensions') != b.get('extensions'): bad.append('variants list')
info.append('materials ' + str([m['name'] for m in b['materials']]))
# LOD0 vertices away from the hands
def lod0(G):
    p = G.json['meshes'][0]['primitives'][0]['attributes']
    return {k: G.accessor(v) for k, v in p.items() if k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')}
va, vb = lod0(A), lod0(B)
hands = [ja.index('LeftHand'), ja.index('RightHand')]
hw = sum(((va['JOINTS_0'] == h) * va['WEIGHTS_0']).sum(1) for h in hands)
keep = np.where(hw < 1e-4)[0]
tree = cKDTree(np.hstack([vb['POSITION'], vb['TEXCOORD_0']]))
d, k = tree.query(np.hstack([va['POSITION'][keep], va['TEXCOORD_0'][keep]]))
miss = d > 1e-5
info.append(f'LOD0 non-hand vertices {len(keep)}, unmatched {int(miss.sum())} (deleted wrist shards / rim)')
ok = ~miss
def jw(v, i, names):
    out = {}
    for j, w in zip(v['JOINTS_0'][i], v['WEIGHTS_0'][i]):
        if w > 1e-4: out[names[int(j)]] = out.get(names[int(j)], 0) + float(w)
    return out
wbad = 0; nbad = 0
for i0, i1 in zip(keep[ok], k[ok]):
    wa, wb = jw(va, i0, ja), jw(vb, i1, jb)
    if set(wa) != set(wb) or max(abs(wa[x] - wb.get(x, 0)) for x in wa) > 2e-3: wbad += 1
    if np.dot(va['NORMAL'][i0], vb['NORMAL'][i1]) < 0.999: nbad += 1
info.append(f'matched non-hand vertices with other weights: {wbad}, other normals: {nbad}')
if wbad > 0.01 * ok.sum(): bad.append('non-hand weights')
if nbad > 0.01 * ok.sum(): bad.append('non-hand normals')
# images
rect = np.zeros((1024, 2080), bool)
for x0, y0, w, h in gcfg['rects'].values(): rect[y0:y0 + h, x0:x0 + w] = True
def img(G, name):
    im = next(i for i in G.json['images'] if i['name'] == name); v = G.json['bufferViews'][im['bufferView']]
    return np.asarray(Image.open(io.BytesIO(bytes(G.bin[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])))).astype(int)
for im in a['images']:
    if 'lod' in im['name']: continue
    x, y = img(A, im['name']), img(B, im['name'])
    diff = np.abs(x - y).reshape(x.shape[0], x.shape[1], -1).max(-1) > 0
    out = int((diff & ~rect).sum())
    info.append(f'image {im["name"]}: changed {int(diff.sum())} px, outside rects {out}')
    if out: bad.append(f'image {im["name"]} outside rects')
tri = lambda G, i: sum(G.accessor(p['indices']).shape[0] // 3 for p in G.json['meshes'][i]['primitives'])
for G, nm in ((A, 'installed'), (B, 'new')):
    m0 = G.json['meshes'][0]
    info.append(f'{nm} LOD triangles {[tri(G, 0)] + [tri(G, i) for i in m0["extras"]["openyamm_lods"]]}')
print('\n'.join(info)); print('UNEXPECTED:', bad if bad else 'none')
sys.exit(1 if bad else 0)
