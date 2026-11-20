"""Forad's bracer lining on a cream sleeve (PeasantM8d, 2026-11-02): sleeve_lining.py gave Forad's lining and cuff-rim faces
one dark texel of his dark bracers (dark_rgb 0,0,0); on PeasantM8d's cream linen cuffs that showed as a black fin at the
wrist. The faces that share one single texel (zero UV area) on the body are pointed instead at the centre texel of the
cuff face (body face within 7 cm of that side's hand joint) whose colour is nearest the cuffs' median.
Args (Blender): <in blend> <out blend> <body base colour png>"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = body.data; uv = me.uv_layers['UVMap']
img = bpy.data.images.load(a[2]); W, H = img.size
px = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
for s in 'LR':
    hj = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local
    deg, cuff = [], []
    for f in me.polygons:
        if hd[f.index] or hn[f.index]: continue
        c = body.matrix_world @ f.center
        if (c - hj).length > 0.09: continue
        us = np.array([tuple(uv.data[l].uv) for l in f.loop_indices])
        if np.ptp(us, 0).max() < 1e-6: deg.append(f)
        elif (c - hj).length < 0.07:
            m = us.mean(0); cuff.append((f, m, px[min(H - 1, int(m[1] * H)), min(W - 1, int(m[0] * W)), :3]))
    cols = np.array([c[2] for c in cuff]); med = np.median(cols, 0)
    best = min(cuff, key=lambda c: float(np.linalg.norm(c[2] - med)))
    for f in deg:
        for l in f.loop_indices: uv.data[l].uv = tuple(best[1])
    print('LINING', s, 'faces', len(deg), 'cuff faces', len(cuff), 'texel rgb', np.round(best[2] * 255).astype(int).tolist())
bpy.ops.wm.save_as_mainfile(filepath=a[1])
