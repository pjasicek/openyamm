#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Ram LOD0 (primitives Ram_A = the sheep body, RamHorn = the two horns) for
mpqem.py: work/glb_sets_<tag>.npz (keep, group, lining, lined + labels), faces in primitive order (Ram_A then RamHorn).
Animal reading of the face rule (assignment): the head stays exact (eyes, muzzle, nostrils, mouth cavity, horns, ears):
- exact: every horn face (RamHorn kept whole in mpqem.py); the face = head-weighted skin (Xheadpiv, Xhead, Xjawpiv, ears
  summed weight > 0.5) whose texels are not wool (region mask R < WOOL at the face's corners and centre: head skin G, pink B,
  unmasked eyes/mouth), grown FACE_RING rings; every ear face; the horn contact (body faces within HORN_D of a horn vertex);
  hooves (dominant Xffoot*/Xbfoot*, rigid on the foot bones) plus HOOF_RING rings; soles (faces within SOLE of the floor);
- group HEADWOOL (if > 0): the head-weighted wool behind the face (poll and neck cap); else exact;
- group 0: the rest (body wool, legs, tail).
Usage: ram_sets.py <tag>   (env FACE_RING, HOOF_RING, SOLE, WOOL, HORN_D, HEADWOOL)"""
import io, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
FACE_RING = int(E('FACE_RING', '2')); HOOF_RING = int(E('HOOF_RING', '1')); SOLE = float(E('SOLE', '0.02'))
WOOL = float(E('WOOL', '0.5')); HORN_D = float(E('HORN_D', '0.02')); HEADWOOL = int(E('HEADWOOL', '1'))
tag = sys.argv[1]
doc, b = gb.read(HERE / 'before' / 'mm9_ram.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Ram' and 'mesh' in n)
prs = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in prs] == ['Ram_A', 'RamHorn']
pr, hp = prs
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W, UV = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float), pr['TEXCOORD_0']
nF = len(T)
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
fw /= 3
dom = fw.argmax(1); cen = P[T].mean(1)
mat = next(m for m in doc['materials'] if m['name'] == 'Ram_A')
ii = doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']; v = doc['bufferViews'][doc['images'][ii]['bufferView']]
mask = np.asarray(Image.open(io.BytesIO(b[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])).convert('RGBA'), np.float32) / 255
H, Wd = mask.shape[:2]


def sample(uv):
    x = np.clip((uv[..., 0] * Wd).astype(int), 0, Wd - 1); y = np.clip((uv[..., 1] * H).astype(int), 0, H - 1)
    return mask[y, x]


wool = np.max(np.stack([sample(UV[T[:, k]])[:, 0] for k in range(3)] + [sample(UV[T].mean(1))[:, 0]], 1), 1)


def grow(sel, rings, within=None):
    sel = sel.copy()
    for _ in range(rings):
        vm = np.zeros(nW, bool); vm[FT[sel].ravel()] = True; add = vm[FT].any(1)
        sel |= add if within is None else (add & within)
    return sel


ji = lambda names: [joints.index(n) for n in names]
headw = fw[:, ji(('Xheadpiv', 'Xhead', 'Xjawpiv', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01'))].sum(1)
head = headw > 0.5
ears = np.isin(dom, ji(('Xearpiv', 'Xear', 'Xearpiv01', 'Xear01')))
face = grow((head & (wool < WOOL)) | ears, FACE_RING)
hd, _ = cKDTree(hp['POSITION'].astype(float)).query(cen)
horn_c = np.zeros(nF, bool)
for k in range(3):
    d_, _ = cKDTree(hp['POSITION'].astype(float)).query(P[T[:, k]]); horn_c |= d_ < HORN_D
hoof = grow(np.isin(dom, ji(('Xffoot', 'Xffoot01', 'Xbfoot', 'Xbfoot01'))), HOOF_RING)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
keep = face | horn_c | hoof | sole
group = np.zeros(nF, int)
if HEADWOOL:
    group[head & ~keep] = HEADWOOL
else:
    keep |= head
nH = len(hp['T'])
print(f'Ram_A faces {nF}: head {int(head.sum())} (face exact {int(face.sum())}, of it ears {int(ears.sum())}; head wool '
      f'{int((head & ~keep).sum())}), horn contact {int(horn_c.sum())}, hooves {int(hoof.sum())}, soles {int(sole.sum())} '
      f'(floor {floor:.4f}); RamHorn {nH} exact')
for gl in np.unique(group):
    print(f'group {gl}: free {int(((group == gl) & ~keep).sum())} (of {int((group == gl).sum())})')
K = np.concatenate([keep, np.ones(nH, bool)]); Z = np.zeros(nF + nH, bool)
print(f'protected share {K.sum() / len(K) * 100:.1f} % ({int(K.sum())} of {len(K)}); free {int((~K).sum())}; '
      f'-15 % = {int(round(0.15 * len(K)))} tris = {0.15 * len(K) / max(1, (~K).sum()) * 100:.0f} % of the free faces')
pad = lambda a: np.concatenate([a, np.zeros(nH, a.dtype)])
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=pad(group), lining=Z, lined=Z, face=pad(face), head=pad(head),
         ears=pad(ears), horn_c=pad(horn_c), hoof=pad(hoof), sole=pad(sole), wool=pad(wool))
