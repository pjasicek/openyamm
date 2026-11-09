"""Where each shell lies along each arm (step1.blend): t along Meshy shoulder -> far tip of the hand, per piece the
t-range and the radial size per t bin. Prints a table per side. Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in ob.data.vertices])
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}
for s, hand, brac in (('R', 4, 9), ('L', 5, 10)):
    S = M[f'{s}_UpperArm']; Wm = M[f'{s}_Hand']
    d = (Wm - S) / np.linalg.norm(Wm - S)
    hv = co[pv == hand]; tip = hv[np.argmax((hv - S) @ d)]
    L = np.linalg.norm(tip - S); d = (tip - S) / L
    t = (co - S) @ d / L
    r = np.linalg.norm((co - S) - np.outer((co - S) @ d, d), axis=1)
    print('ARMLEN', s, round(float(L), 3))
    for p in (0, brac, hand):
        m = (pv == p) & (r < 0.09) & (t > 0.0) & (t < 1.01)
        if not m.any():
            continue
        print('PIECE', s, p, 't', round(float(t[m].min()), 3), round(float(t[m].max()), 3))
        row = []
        for b in np.arange(0.4, 1.0, 0.03):
            mb = m & (t >= b) & (t < b + 0.03)
            row.append(f'{b:.2f}:{(r[mb].mean() * 100 if mb.any() else 0):.1f}')
        print('  radius cm', ' '.join(row))
