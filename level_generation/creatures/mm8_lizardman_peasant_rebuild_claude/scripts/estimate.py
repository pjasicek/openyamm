#!/usr/bin/env python3
"""Body placement and limb centrelines of the Meshy body, for the joint estimates in fit_config_liz.json.
Placement (also used by fit_liz.py): Blender space (Z up, -Y front), height H, feet on the MM9 floor, x centred on the
torso, y on the torso centre. Prints ring centres along each limb; draws them on front/side views (review/est.png)."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glb_pose as gp, motion_frames
H, FLOOR = 1.70, -0.80
g = gp.Glb(HERE / 'meshy/smart_v1/model_urls_glb.glb')
for n in g.json['nodes']:
    if 'matrix' in n:
        M = np.array(n.pop('matrix')).reshape(4, 4).T; sc = np.linalg.norm(M[:3, :3], axis=0)
        n['translation'] = M[:3, 3].tolist(); n['scale'] = sc.tolist(); n['rotation'] = gp.matrix_quaternion(M[:3, :3] / sc).tolist()
m = gp.Model(g); w = m.world({})
P, T = [], []; off = 0
for pr in m.primitives:
    M = w[pr['node']]; p = pr['positions'] @ M[:3, :3].T + M[:3, 3]; P.append(p); T.append(pr['triangles'] + off); off += len(p)
G = np.concatenate(P); T = np.concatenate(T)
B = np.stack([G[:, 0], -G[:, 2], G[:, 1]], 1)            # glTF -> Blender
s = H / (B[:, 2].max() - B[:, 2].min()); B *= s; B[:, 2] += FLOOR - B[:, 2].min()
tor = (B[:, 2] > FLOOR + 0.9) & (B[:, 2] < FLOOR + 1.2) & (np.abs(B[:, 0]) < 0.15)
B[:, 0] -= 0.5 * (B[tor, 0].min() + B[tor, 0].max()); B[:, 1] -= 0.5 * (B[tor, 1].min() + B[tor, 1].max())
np.savez(HERE / 'work/placed.npz', co=B, tri=T, scale=s)
out = {}
def rings(sel, axis_pts, n=40, r=0.12):
    a, b = np.array(axis_pts[0]), np.array(axis_pts[1]); ax = (b - a) / np.linalg.norm(b - a); L = np.linalg.norm(b - a)
    res = []
    for t in np.linspace(0, L, n):
        q = B[sel]; tt = (q - a) @ ax; m_ = np.abs(tt - t) < 0.012
        if m_.sum() < 5: res.append(None); continue
        qq = q[m_]; perp = qq - a - np.outer((qq - a) @ ax, ax); d = np.linalg.norm(perp - perp.mean(0), axis=1)
        qq = qq[d < r]
        if len(qq) < 3: res.append(None); continue
        res.append((round(float(t), 3), (0.5 * (qq.min(0) + qq.max(0))).round(3).tolist(), round(float(np.ptp(qq[:, 0]) if abs(ax[0]) < 0.5 else np.ptp(qq[:, 2])), 3)))
    return res
# arms: from the shoulder region to the farthest hand point on each side
for sx, nm in ((1, 'L'), (-1, 'R')):
    side = (np.sign(B[:, 0]) == sx)
    tip = B[side][np.argmax(np.abs(B[side, 0]))]
    sh = np.array([sx * 0.17, 0.0, FLOOR + 1.28])
    out['arm_' + nm] = rings(side & (np.abs(B[:, 0]) > 0.12), (sh, tip), 36, 0.09)
    out['tip_' + nm] = tip.round(3).tolist()
    # legs: vertical rings from z = FLOOR+0.95 down
    res = []
    for z in np.arange(FLOOR + 0.95, FLOOR - 0.001, -0.025):
        m_ = side & (np.abs(B[:, 2] - z) < 0.012) & (np.abs(B[:, 0]) > 0.015)
        if m_.sum() < 5: continue
        q = B[m_]; res.append((round(float(z), 3), (0.5 * (q.min(0) + q.max(0))).round(3).tolist(), round(float(np.ptp(q[:, 1])), 3)))
    out['leg_' + nm] = res
for k, v in out.items():
    print(k); [print('  ', x) for x in (v if isinstance(v, list) and v and isinstance(v[0], (tuple, type(None))) else [v])]
cells = []
for yaw in (0, 1.57):
    cam = np.stack([B[:, 0], B[:, 2], B[:, 1]], 1) @ motion_frames.view(yaw, 0).T   # to a y-up frame for the renderer
    lo, hi = cam.min(0), cam.max(0); c = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    img = motion_frames.draw(cam, T, None, c, span, 700); img = Image.blend(img, Image.new('RGB', img.size, 'white'), 0.4)
    d = ImageDraw.Draw(img); sc = 690 / span
    for k, v in out.items():
        if not k.startswith(('arm', 'leg')): continue
        for x in v:
            if x is None: continue
            p = np.array(x[1]); q = np.array([p[0], p[2], p[1]]) @ motion_frames.view(yaw, 0).T
            X, Y = 350 + (q[0] - c[0]) * sc, 350 - (q[1] - c[1]) * sc; d.ellipse([X - 2, Y - 2, X + 2, Y + 2], fill=(255, 0, 0))
    cells.append(img)
sh = Image.new('RGB', (1400, 700)); sh.paste(cells[0], (0, 0)); sh.paste(cells[1], (700, 0)); sh.save(HERE / 'review/est.png')
