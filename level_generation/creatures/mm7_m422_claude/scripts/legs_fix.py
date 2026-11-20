"""Knees and ankles on the leg mesh's centre line (after joints_fix.py; edits work/joints_final.json in place).
Meshy's auto-rig saw the coat over the knees and put both knee joints 8.5 cm in FRONT of the leg mesh centre (at the
front surface of the trousers); the calf then swung about the knee's front and swept through the back of the coat
skirt in the walk (review/poke/). The legs are their own Smart Topology piece (creature.json 'leg_piece'): per side,
the vertices of that piece within 1.5 cm of the joint height on that side of x = 0 give the cross-section, and the
joint moves to its bounding-box centre in x and y (height kept). Args: -- <step1 blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
me = bpy.data.objects['Body'].data
pv = np.array([a.value for a in me.attributes['piece'].data]); co = np.array([v.co[:] for v in me.vertices])
LEG = int(cfg.C.get('leg_piece', 2))
p = os.path.join(HERE, 'work', 'joints_final.json'); d = json.load(open(p)); J = d['joints']
rep = {}
for s, sg in (('L', 1), ('R', -1)):
    for b in ('Calf', 'Foot'):
        j = np.array(J[f'{s}_{b}'])
        m = (pv == LEG) & (np.abs(co[:, 2] - j[2]) < 0.015) & (np.sign(co[:, 0]) == sg)
        assert m.sum() > 8, (s, b, int(m.sum()))
        c = (co[m].min(0) + co[m].max(0)) / 2
        new = [float(c[0]), float(c[1]), float(j[2])]
        rep[f'{s}_{b}'] = round(float(np.linalg.norm(np.array(new) - j)) * 100, 1)
        J[f'{s}_{b}'] = new
d.setdefault('report', {})['legs_fix_moved_cm'] = rep
json.dump(d, open(p, 'w'), indent=1)
print('LEGSFIX moved cm', rep)
