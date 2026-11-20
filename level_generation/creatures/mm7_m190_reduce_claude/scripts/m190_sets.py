#!/usr/bin/env python3
"""Keep set and region groups for the m190 Dwarf ladder (work/pieces.npy from m190_pieces.py, soles.npy, gold.npy,
visible_all.npy, groups.npz).
Kept exactly: both hands (shells 4/5, the six-finger fix and the fitted fist) and every face touching a vertex with hand +
finger weight > 0.3 (bracer ends); the eyes (24/25); the mail-skirt hem band; the braids and braid ends (9/10, 21/22: thin); the shoulder-guard
rims (19/20); the buckle (23); the boot soles (faces below 6 cm); the gold (work/gold.npy: helmet rim and ridge, horn
rings, bracer and boot rims, buckle) (M190_RING=1: with the faces sharing an edge with it in the same shell); the helmet top spike (helmet faces
above M190_SPIKE_Z, default 1.255 m) and the horn tips (horn faces above M190_TIP_Z, default 1.33 m); the face front
(head-set faces of the torso shell within M190_FACE_R, default 0.07 m, of the face centre and in front of y = -0.07).
Groups (decimated on their own): 1 visible beard and hair (head set), 2 hidden head skin (head set, never seen in work/visible_all.npy: scalp under
the helmet), 3 helmet dome, 4 horns, 5 shoulder guards, 6 mail skirt, 7 ragged skirt, 8 hidden body faces (never seen
from any view), 9 visible torso, 10 bare upper arms; label 0 (legs, boots, bracers) takes the rest of the ladder budget.
Usage: m190_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
E = lambda k, x: float(os.environ.get(k, x))
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); gold = np.load('work/gold.npy')
seen = np.load('work/visible_all.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); headset = (u > 0.51) & (p == 0)
ring = np.zeros(len(f), bool)
for piece in np.unique(p[gold]):  # faces sharing an edge with a gold face of the same shell
    pv = np.zeros(len(v), bool); pv[np.unique(f[gold & (p == piece)])] = True
    ring |= (p == piece) & (pv[f].sum(1) >= 2)
face = headset & (np.linalg.norm(c - np.array([-0.003, -0.12, 1.09]), axis=1) < E('M190_FACE_R', '0.07')) & (c[:, 1] < -0.07)
spike = (p == 8) & (v[f][..., 2].min(1) > E('M190_SPIKE_Z', '1.255'))
tips = np.isin(p, (17, 18)) & (v[f][..., 2].max(1) > E('M190_TIP_Z', '1.33'))
if os.environ.get('M190_RING', '0') != '1':  # kept faces are fixed boundaries of the cut anyway
    ring[:] = False
keep = (np.isin(p, (4, 5, 24, 25, 9, 10, 21, 22, 19, 20, 23)) | (hand[f] > 0.3).any(1) | soles | gold | ring | spike
        | tips | face)
# ragged skirt hem teeth (faces with a vertex below M190_HEM_Z, default 0.50 m): the teeth shorten and swing apart at a cut
hem = (p == 3) & (v[f][..., 2].min(1) < E('M190_HEM_Z', '0.50'))
if os.environ.get('M190_HEM', '1') == '1':
    keep |= hem
# mail skirt hem: faces within M190_MAIL_H (default 0.03 m) of the mail skirt's lowest point in their 15-degree sector
# about the body axis (a uniform cut dented the front hem, review/glbclose/sheet_i87_legs.png)
mv = np.unique(f[p == 7]); axis = v[mv, :2].mean(0)
az = np.arctan2(*(v[:, :2] - axis).T[::-1]); sector = ((az + np.pi) / (2 * np.pi) * 24).astype(int) % 24
low = np.full(24, 9.0); np.minimum.at(low, sector[mv], v[mv, 2])
mail_hem = (p == 7) & (v[:, 2] < low[sector] + E('M190_MAIL_H', '0.03'))[f].all(1)
if os.environ.get('M190_MAIL_HEM', '1') == '1':
    keep |= mail_hem
extra = os.environ.get('M190_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[headset & (seen > 0)] = 1; groups[headset & (seen == 0)] = 2
for lab, pcs in ((3, (8,)), (4, (17, 18)), (5, (13, 14)), (6, (7,)), (7, (3,))):
    groups[np.isin(p, pcs)] = lab
groups[(groups == 0) & (seen == 0)] = 8
groups[(groups == 0) & (p == 0) & ~headset] = 9          # visible torso (body set)
groups[(groups == 0) & np.isin(p, (15, 16))] = 10        # bare upper arms
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(face', int(face.sum()), 'hem', int(hem.sum()), 'mail hem', int(mail_hem.sum()), 'gold+ring', int((gold | ring).sum()), 'spike', int(spike.sum()),
      'tips', int(tips.sum()), ')', {k: int(((groups == k) & ~keep).sum()) for k in range(11)})
