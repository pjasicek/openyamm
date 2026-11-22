"""Label every loose part of the witch body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 body shells (P00 torso+head+robe, P01 legs, P08/P09 arms, P02/P03 hands, P05/P06 boots): Meshy weights + rules
1 hair strand card (the white mane: small open shells above the shoulders)
2 head hard surface (P04 horned mask crown, P07 jaw/collar piece, P14 forehead gem, small pieces on the face)
3 front panel (P10, black banded apron) and its gold bands (thin wide strips on its face)
4 chest beads (three blue beads at z ~1.21)
5 wrist studs (P11 left gauntlet gem, P13 right wrap stud)
6 boot spikes (small pieces on the boot shafts)
7 loose robe tatters (small shells by the hem): per-vertex copy of the body weights under them
Writes the 'garment' point attribute and work/garments.json; renders a coloured check. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
BODY = {0, 1, 2, 3, 5, 6, 8, 9}
FIXED = {4: 2, 7: 2, 14: 2, 10: 3, 11: 5, 13: 5}
panel = co[pv == 10]; plo, phi = panel.min(0), panel.max(0)
lab = {}
for p in sorted(set(pv.tolist())):
    m = pv == p; c = co[m].mean(0); lo, hi = co[m].min(0), co[m].max(0); ext = hi - lo
    if p in BODY:
        g = 0
    elif p in FIXED:
        g = FIXED[p]
    elif plo[0] - 0.02 < lo[0] and hi[0] < phi[0] + 0.02 and plo[2] - 0.02 < lo[2] and hi[2] < phi[2] + 0.02 \
            and c[1] < plo[1] + 0.04 and ext[2] < 0.04:
        g = 3                                              # gold bands on the panel
    elif 1.15 < c[2] < 1.27 and c[1] < -0.17 and ext.max() < 0.07:
        g = 4                                              # chest beads
    elif c[2] < 0.45:
        g = 6                                              # boot spikes
    elif c[2] > 1.30:
        # face pieces (eyes, fangs) sit inside the mask's front; everything else up there is mane
        g = 2 if (ext.max() < 0.035 and c[1] < -0.2) else 1
    else:
        g = 7                                              # loose robe tatters below the shoulders
    lab[p] = g
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
by = {}
for p, g in lab.items():
    by.setdefault(g, []).append(p)
print('GARMENT pieces', {g: len(v) for g, v in sorted(by.items())}, 'verts', {g: int((gv == g).sum()) for g in range(8)})
print('GARMENT non-hair', {g: v for g, v in by.items() if g not in (0, 1)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
cols = [(0.75, 0.6, 0.5), (0.3, 0.4, 0.95), (0.95, 0.75, 0.1), (0.2, 0.8, 0.3), (0.9, 0.2, 0.2), (0.9, 0.3, 0.8),
        (0.1, 0.9, 0.9), (0.2, 0.2, 0.2)]
ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'POINT')
for i in range(nv):
    ca.data[i].color = (*cols[gv[i]], 1)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
common.render_views(os.path.join(common.REVIEW, 'garments'), 0.92, 1.95, views=('front', 'left', 'back'), resolution=(500, 800), distance=20)
