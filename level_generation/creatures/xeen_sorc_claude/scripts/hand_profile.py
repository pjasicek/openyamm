"""Ring perimeter profile of each hand shell along the shoulder->wrist direction (find the real wrist). Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv[:sys.argv.index('--') + 1] + sys.argv[sys.argv.index('--') + 1:]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fit_witch_joints.py')).read().split('J = {k: v.copy()')[0])
JF = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints'].items()}
for s in ('R', 'L'):
    S, Wr = M[f'{s}_UpperArm'], JF[f'{s}_Hand']
    d = (Wr - S) / np.linalg.norm(Wr - S)
    Hs = shell({HAND[s]}); Ah = shell({ARM[s]})
    out = []
    for k in np.arange(-0.06, 0.16, 0.01):
        q = Wr + d * k
        rh = [r for r in rings(Hs, q, d) if np.linalg.norm(r[0] - q) < 0.06]
        ra = [r for r in rings(Ah, q, d) if np.linalg.norm(r[0] - q) < 0.06]
        out.append(f"{k*100:+.0f}:{(max(r[1] for r in rh)*100 if rh else 0):.0f}/{(max(r[1] for r in ra)*100 if ra else 0):.0f}/{len(rh)}")
    print('HANDPROF', s, ' '.join(out))
