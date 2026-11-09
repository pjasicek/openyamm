#!/usr/bin/env python3
"""Per-face region labels (work/groups.npy) and the exact-keep mask (work/keep_base.npy) for the MM7 Monk.
The source GLB has no part labels; work/face_labels.npz carries the production master's garment and piece per face
(mm7_m290_claude/work/rig_v6.blend, the same rest geometry, matched by face centre; max 0.001 mm).
Labels: 1 visible face (head piece, ray escapes: face, ears, neck front), 2 hidden head (back of the head and the
cropped hair inside the hood), 3 hands (rigid pieces; shrunk into the sleeves while folded), 4 hood, cowl, top and
wide sleeves, 5 robe skirt, 6 shins (inside the robe).
Kept exactly: eyes (garment 4), the rope's knotted ends (garment 8, thin tubes), the painted pale strips on the robe
(hood lining edge, the rope band at the waist: region mask R < 0.5 on robe faces), the sandals (shin/sandal faces
below 12 cm) and the skirt's hem band (below 12 cm)."""
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
L = np.load('work/face_labels.npz'); g, p, R = L['garment'], L['piece'], L['R']
vis = np.load('work/head_visible.npy')
grp = np.zeros(len(f), int)
grp[p == 1] = np.where(vis[p == 1], 1, 2)
grp[np.isin(p, [3, 4])] = 3
grp[g == 1] = 4
grp[g == 2] = 5
grp[g == 15] = 6
keep = (g == 4) | (g == 8) | (np.isin(g, [1, 2]) & (R < 0.5)) | ((g == 15) & (c[:, 2] < 0.12)) | ((g == 2) & (c[:, 2] < 0.12))
grp[(grp == 0)] = 4
np.save('work/groups.npy', grp); np.save('work/keep_base.npy', keep)
print('GROUPS', {int(k): int((grp == k).sum()) for k in np.unique(grp)}, 'kept', int(keep.sum()),
      {int(k): int((keep & (grp == k)).sum()) for k in np.unique(grp)})
