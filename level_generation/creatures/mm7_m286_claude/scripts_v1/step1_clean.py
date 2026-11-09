"""Step 1 of the m286 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P153; H = 2.1 m to the horn tips,
the head top at about 1.92 m like the humanoid set's proportions; positions below are quoted at 2.5 m and scaled).
P00 is the body shell (skin, head, arms, hands, legs with the fused fur kilt). Named parts (examine_parts.py report):
P01/P02 horns, P04 nose ring, P05/P06 wrist bands, P07 belt, P08-P11 eyes and lids, P12 nostril piece; the belt beads
and the wrist spikes are small closed pieces at the belt (z 1.24-1.38) and at the bands (|x| > 0.5).
Everything else (~130 cards) is Meshy's mane: a cape of cards standing up to 30 cm off the back and hanging to the
thighs, with one long strip (P03) down to the knees. The native mane is a shaggy strip on the neck and upper back
(m286sa2-4), so the cape is cut back to the cards that lie on the head, neck and upper back: every vertex within
MANE_GAP of the body shell and the card's lowest point above MANE_Z. The retexture paints the rest of the mane.
Joins the kept parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (rest positions).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
# thresholds were read at 2.5 m to the horn tips; the parts file is normalised by examine_parts.py's H (2.1 m)
allz = np.concatenate([[(o.matrix_world @ v.co).z for v in o.data.vertices] for o in P.values()])
S = float(allz.max() - allz.min()) / 2.5
MANE_GAP = float(os.environ.get('MANE_GAP', '0.05')) * S
MANE_Z = float(os.environ.get('MANE_Z', '1.55')) * S
NAMED = {'P00', 'P01', 'P02', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12'}
body = P['P00']
bco = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
kd = KDTree(len(bco))
for i, c in enumerate(bco):
    kd.insert(c, i)
kd.balance()
removed, kept_mane, kept_small = [], [], []
for n, o in list(P.items()):
    if n in NAMED:
        continue
    co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    c = co.mean(0)
    belt = 1.22 * S <= c[2] <= 1.40 * S and abs(c[0]) < 0.26 * S and c[1] < 0.15 * S and np.ptp(co[:, 2]) < 0.1 * S \
        and len(co) < 25
    spike = abs(c[0]) > 0.5 * S and 1.05 * S < c[2] < 1.5 * S
    if belt or spike:
        kept_small.append(n)
        continue
    gap = max(kd.find(p)[2] for p in co)
    if n == 'P03' or gap > MANE_GAP or co[:, 2].min() < MANE_Z:
        removed.append(n)
        bpy.data.objects.remove(P.pop(n), do_unlink=True)
    else:
        kept_mane.append(n)
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN parts', len(P), 'mane kept', len(kept_mane), 'removed', len(removed), 'belt/spikes', len(kept_small),
      'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co),
      'height', round(float(co[:, 2].max() - co[:, 2].min()), 4))
print('CLEAN mane', ' '.join(sorted(kept_mane, key=lambda s: int(s[1:]))))
print('CLEAN small', ' '.join(sorted(kept_small, key=lambda s: int(s[1:]))))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
