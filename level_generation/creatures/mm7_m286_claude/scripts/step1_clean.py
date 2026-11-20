"""Step 1 of the m286 v2 Smart Topology return (work/st_v2_parts.blend, loose parts P00..P93, 2.1 m to the horn tips;
examine_parts.py H=2.1). Part map (examine report, review/st_v2_parts_*.png):
  P00 body shell (skin, head, HORNS fused in, arms, hands, goat legs)     P01 fur kilt (open shell)
  P02 mane sheet down the back                                            P03 nose ring
  P04 right / P05 left wrist band                                         P06 belt, P13 buckle
  P07/P08 ears, P09 forelock, P10/P11 eyes, P14 snout piece, P19/P20 brow tufts
  P12 front loincloth flap                                                beads: small closed pieces at the belt
  spikes: small pieces at the bands (|x| > 0.42, z 0.85-1.15)            everything else: mane cards
- Mane: cards centred more than MANE_SIDE off the midline below the crown are dropped (Meshy fanned them beside the
  neck into a ruff; the native shows almost no mane from the front, m286sa0); the retexture paints the mane there.
  The native mane is a shaggy layer about 0.055 H (~10 cm) thick on the neck and back (m286sa2-sa4); Meshy's
  cards stand up to 20 cm off. Every mane vertex is pulled toward its nearest body-shell point, its gap scaled by
  MANE_K (and capped at MANE_CAP, less beside the neck), so the cards lie on the body as a shaggy layer; before that the mane is narrowed toward
  the midline by MANE_XK (the native shows only a little fur beside the jaw from the front).
- Horns: the native horn tips rise 0.189 H above the skull top; Meshy's 0.162 H. The fused horn vertices (P00 above
  the skull's sides) are stretched about each horn root by HORN_K, ramped in over the first 4 cm, so the root stays.
Joins the kept parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (rest positions).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
MANE_K = float(os.environ.get('MANE_K', '0.45'))
MANE_CAP = float(os.environ.get('MANE_CAP', '0.09'))
MANE_CROWN = float(os.environ.get('MANE_CROWN', '9'))          # v2: crown cards are compressed too (they stuck 20 cm back)
MANE_SIDE = float(os.environ.get('MANE_SIDE', '0.16'))
MANE_XK = float(os.environ.get('MANE_XK', '0.7'))               # the sheet framed the head from the front: narrowed
HORN_K = float(os.environ.get('HORN_K', '1.15'))
NAMED = {'P00', 'P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'P14',
         'P19', 'P20'}
body = P['P00']
bco = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
kd = KDTree(len(bco))
for i, c in enumerate(bco):
    kd.insert(c, i)
kd.balance()
mane, small, moved, dropped = [], [], [], []
for n, o in list(P.items()):
    if n in NAMED and n != 'P02':
        continue
    co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    c = co.mean(0)
    if n != 'P02':
        if abs(c[0]) > 0.42 and 0.85 < c[2] < 1.15:
            small.append(n); continue                                      # band spikes
        if c[2] < 1.1 and abs(c[0]) < 0.3 and np.ptp(co, 0).max() < 0.05:
            small.append(n); continue                                      # belt beads
    if n != 'P02' and abs(c[0]) > MANE_SIDE and c[2] < 1.75:
        dropped.append(n)                                                  # ruff beside the neck and face
        bpy.data.objects.remove(P.pop(n), do_unlink=True)
        continue
    mane.append(n)
    if co[:, 2].min() > MANE_CROWN:
        continue                                                           # crown cards stay
    mw = o.matrix_world; mi = mw.inverted()
    gaps = []
    for v in o.data.vertices:
        p = np.array(mw @ v.co)
        p[0] *= MANE_XK
        q, _, d = kd.find(p)
        q = np.array(q)
        # lateral cards (beside the neck and face) lie flatter: the native shows no ruff from the front
        cap = MANE_CAP * float(np.clip(1 - (abs(p[0]) - 0.10) / 0.10, 0.25, 1))
        g = min(d * MANE_K, cap)
        newp = q + (p - q) / max(d, 1e-6) * g if d > 1e-6 else p
        v.co = mi @ type(v.co)(newp)
        gaps.append(g)
    moved.append((n, round(float(max(gaps)), 3)))
# horns: P00 vertices above the skull's sides
skull_top = bco[np.abs(bco[:, 0]) < 0.04, 2].max()
horn = (bco[:, 2] > skull_top - 0.10) & (np.abs(bco[:, 0]) > 0.125) | (bco[:, 2] > skull_top + 0.025)
nh = 0
for sd in (-1, 1):
    m = horn & (np.sign(bco[:, 0]) == sd)
    pts = bco[m]
    # root: the lowest horn vertices, where the horn leaves the side of the skull (the tips curve back inward)
    root = pts[pts[:, 2] < pts[:, 2].min() + 0.05].mean(0)
    d = np.linalg.norm(pts - root, axis=1)
    k = 1 + (HORN_K - 1) * np.clip(d / 0.04, 0, 1)
    new = root + (pts - root) * k[:, None]
    for i, p in zip(np.flatnonzero(m), new):
        body.data.vertices[i].co = body.matrix_world.inverted() @ type(body.data.vertices[i].co)(p)
    nh += int(m.sum())
bco2 = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
print('CLEAN horns', nh, 'verts stretched x', HORN_K, 'skull top', round(float(skull_top), 3), 'horn tips',
      round(float(bco[:, 2].max()), 3), '->', round(float(bco2[:, 2].max()), 3))
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
# 'orig_co' = the geometry Meshy's auto-rig saw (export_clean.py of the pre-reshape step1): build_rig.py matches its
# weights there. Then the lower-body slimming (reshape.py; meshy_joints.py moves Meshy's joints the same way).
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
if os.environ.get('RESHAPE', '1') == '1':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import reshape
    new = reshape.arm_apply(reshape.apply(co))
    for v, p in zip(me.vertices, new):
        v.co = p
    print('CLEAN reshape: lower body x scaled', reshape.K_LEG, '(legs)', reshape.K_HIP, '(hips/kilt), arms radial',
          reshape.ARM_K, '; max move cm',
          round(float(np.abs(new - co).max()) * 100, 1))
    co = new
print('CLEAN parts', len(P), 'mane cards', len(mane), 'compressed', len(moved), 'beads/spikes', len(small),
      'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co),
      'height', round(float(co[:, 2].max() - co[:, 2].min()), 4))
print('CLEAN mane max gap after', max(g for _, g in moved), 'lateral cards dropped', len(dropped), ' '.join(dropped))
print('CLEAN small', ' '.join(sorted(small, key=lambda s: int(s[1:]))))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
