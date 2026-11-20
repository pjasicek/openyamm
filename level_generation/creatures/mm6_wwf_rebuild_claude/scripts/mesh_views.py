#!/usr/bin/env python3
"""Flat-shaded views of every mesh in a GLB (no skin), glTF Y-up: front, side, back, three-quarter, plus zoom on an
optional point. Usage: mesh_views.py <glb> <out.png> [--zoom x,y,z,span ...]"""
import sys, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp, motion_frames
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('out'); ap.add_argument('--zoom', action='append', default=[])
ap.add_argument('--cell', type=int, default=420); ap.add_argument('--yaws', default='0,1.57,3.14,0.7')
o = ap.parse_args()
g = gp.Glb(o.glb)
for n in g.json['nodes']:
    if 'matrix' in n:
        M = np.array(n.pop('matrix')).reshape(4, 4).T
        n['translation'] = M[:3, 3].tolist(); sc = np.linalg.norm(M[:3, :3], axis=0); n['scale'] = sc.tolist()
        n['rotation'] = gp.matrix_quaternion(M[:3, :3] / sc).tolist()
m = gp.Model(g); w = m.world({})
P, T = [], []; off = 0
for pr in m.primitives:
    M = w[pr['node']]; p = pr['positions'] @ M[:3, :3].T + M[:3, 3]
    P.append(p); T.append(pr['triangles'] + off); off += len(p)
P = np.concatenate(P); T = np.concatenate(T)
print('verts', len(P), 'tris', len(T), 'bbox', P.min(0).round(3), P.max(0).round(3))
cells = []
views = [(float(y), None) for y in o.yaws.split(',')] + [(float(z.split(',')[4]) if len(z.split(',')) > 4 else 0.0, z) for z in o.zoom]
for yaw, z in views:
    rot = motion_frames.view(yaw, 0.1); cam = P @ rot.T
    if z:
        x, y, zz, span = [float(v) for v in z.split(',')[:4]]
        c = (np.array([x, y, zz]) @ rot.T)[:2]
    else:
        lo, hi = cam.min(0), cam.max(0); c = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    img = motion_frames.draw(cam, T, None, c, span, o.cell); ImageDraw.Draw(img).text((4, 4), f'yaw {yaw} {z or ""}', fill=(0, 0, 0)); cells.append(img)
sh = Image.new('RGB', (o.cell * len(cells), o.cell), 'white')
for i, c in enumerate(cells): sh.paste(c, (i * o.cell, 0))
sh.save(o.out)
