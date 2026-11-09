#!/usr/bin/env python3
"""m182 v3b reduction regions (system Python) on work/mesh_in.npz (the welded v3b LOD0): per face, sampled from the
v3b runtime maps at the face's UV corners and centre, plus geometry.
KEEP exactly (work/keep.npy): the v3b wing-root zone (body faces with wing-bone weights, plus one ring), wings (thin closed membranes, kept whole in every LOD as cdr1), every separate piece of
up to 80 faces (dorsal blades, horns, cheek/neck spikes, claws if separate), head faces painted as eye (class 6),
teeth (5), ivory (4), mouth (7) or frill (head region mask A) and their one-ring neighbours, and body faces painted
ivory (claws and spurs, class 4) with their one-ring.
GROUPS (work/groups.npy): 1 = the rest of the head set (skull skin), 2 = the refitted neck join (loft + head stub,
work/v3b/neck_patch.npy matched by position), 0 = the cdr1 body: decimated by the ladder.
Prints face counts per class."""
import json
import numpy as np
from pathlib import Path
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
H = Path(__file__).resolve().parents[1]; P = H.parent; T = P / 'textures/v3'
d = np.load(H / 'work/mesh_in.npz'); v, f, w = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
mat = (w[:, 0, 0] // 2).astype(int); uv = w - np.stack([2.0 * mat, np.zeros_like(mat)], -1)[:, None, :]
samples = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)                    # 3 corners + centre
def sample(img, ch=None):
    a = np.asarray(img); n = a.shape[0]
    px = np.clip((samples[..., 0] * n).astype(int), 0, n - 1); py = np.clip(((1 - samples[..., 1]) * n).astype(int), 0, n - 1)
    s = a[py, px]; return s if ch is None else s[..., ch]
cls = {lab: sample(Image.open(T / f'm182v3_{lab}_material_classes.png')) for lab in ('body', 'head')}
hmask = sample(Image.open(T / 'm182v3_head_region_mask.png').convert('RGBA'), 3)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; small = np.bincount(fl)[fl] <= 80
head, body, wing = mat == 1, mat == 0, mat == 2
feat_head = head & ((np.isin(cls['head'], [4, 5, 6, 7]).sum(1) >= 1) | ((hmask > 127).sum(1) >= 2))
feat_body = body & (cls['body'] == 4).sum(1).__ge__(2)
def ring(sel):
    vs = np.zeros(n, bool); vs[f[sel].ravel()] = True; return vs[f].any(1)
# neck join: v3b patch vertices (master) matched by position
M = np.load(P / 'work/v3b/master_final.npz'); patch = np.load(P / 'work/v3b/neck_patch.npy')
pv = M['co'][patch]; dd, _ = cKDTree(pv).query(v); vpatch = dd < 1e-5
# v3b wing-root zone: body faces with any wing-bone weight (shoulder skin that follows the wing since v3b), one-ring
_, mi = cKDTree(M['co']).query(v); wingw = M['W'][mi][:, [i for i, b in enumerate(M['bones']) if 'Wing' in b]].sum(1)
root = body & (wingw[f] > 1e-4).any(1)
keep = wing | small | ring(feat_head) & head | ring(feat_body) & body | ring(root) & body
groups = np.zeros(len(f), int); groups[head & ~keep] = 1; groups[vpatch[f].all(1) & ~keep] = 2
np.save(H / 'work/keep.npy', keep); np.save(H / 'work/groups.npy', groups)
rep = {'faces': len(f), 'kept': {'wings': int(wing.sum()), 'small_pieces': int((small & ~wing).sum()),
       'head_features_ring': int((ring(feat_head) & head & ~small).sum()), 'body_claws_ring': int((ring(feat_body) & body & ~small).sum()),
       'wing_root_ring': int((ring(root) & body & ~small & ~ring(feat_body)).sum()),
       'total': int(keep.sum())}, 'group1_head_skin': int((groups == 1).sum()), 'group2_neck_join': int((groups == 2).sum()),
       'group0_cdr1_body': int(((groups == 0) & ~keep).sum())}
(H / 'work/regions.json').write_text(json.dumps(rep, indent=1)); print('REGIONS', json.dumps(rep))
