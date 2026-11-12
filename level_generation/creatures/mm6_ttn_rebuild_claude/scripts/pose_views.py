#!/usr/bin/env python3
"""Flat-shaded close-ups of a GLB (motion_frames renderer): every --view is clip@time:joint:yaw:zoom (clip '-' = rest).
    pose_views.py <glb> <out.png> --view -@0:LeftHand:0:0.25 --view Cast@1.9:LeftArm:0.8:0.45 [--cell 300] [--highlight]"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit, motion_frames
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('out')
ap.add_argument('--view', action='append', required=True); ap.add_argument('--cell', type=int, default=300)
ap.add_argument('--highlight', action='store_true'); ap.add_argument('--mark', help='paint triangles whose dominant joint name contains this red'); ap.add_argument('--pitch', type=float, default=0.15)
o = ap.parse_args()
a = motion_audit.Audit(o.glb)
cells = []
for spec in o.view:
    ct, joint, yaw, zoom = spec.split(':')
    clip, t = ct.split('@'); clip = None if clip == '-' else clip; t = float(t)
    posed, scale, palette, world = a.pose(clip, t)
    bad = None
    if o.highlight and clip:
        s1, s2, fold, live = a.deformation(posed, scale, palette)
        bad = live & ((s1 > motion_audit.STRETCH) | (s2 < motion_audit.SQUASH) | fold)
    if o.mark:
        jn_ = np.array([o.mark in a.joint_names[j] if j >= 0 else False for j in a.tri_joint]); bad = jn_
    rot = motion_frames.view(float(yaw), o.pitch); cam = posed @ rot.T
    if joint and joint != '-':
        jn = a.model.joints[a.joint_names.index(joint)]
        centre = (world[jn][:3, 3] @ rot.T)[:2]; span = float(zoom) * a.height
    else:
        lo, hi = cam.min(0), cam.max(0); centre = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    img = motion_frames.draw(cam, a.tris, bad, centre, span, o.cell)
    ImageDraw.Draw(img).text((4, 4), f'{clip or "rest"} {t:.2f}s {joint} y{yaw}', fill=(0, 0, 0))
    cells.append(img)
cols = min(len(cells), 6); rows = (len(cells) + cols - 1) // cols
sheet = Image.new('RGB', (o.cell * cols, o.cell * rows), (255, 255, 255))
for i, img in enumerate(cells):
    sheet.paste(img, ((i % cols) * o.cell, (i // cols) * o.cell))
sheet.save(o.out); print(o.out)
