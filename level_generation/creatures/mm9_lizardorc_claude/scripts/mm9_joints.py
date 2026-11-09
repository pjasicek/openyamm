"""MM9 joints from the true source: world rest matrices (glTF frame), hierarchy, symmetric bind targets."""
import numpy as np, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
def rest():
    m = Model(Glb(HERE / 'source/true/lizardorc_true.glb')); W = m.world({}); doc = m.glb.json
    names = [n.get('name') for n in doc['nodes']]
    par = {}
    for i, n in enumerate(doc['nodes']):
        for c in n.get('children', []): par[names[c]] = names[i]
    return {names[i]: np.array(W[i]) for i in range(len(names))}, par, doc
def sym():
    """Symmetric target joints, left side and centre: MM9 lengths, directions the mean of the left and mirrored right chains."""
    W, par, _ = rest(); X = np.array([-1, 1, 1.])
    P = {n: W[n][:3, 3].copy() for n in W}
    J = {}
    for n in P:
        if ' R ' in n: continue
        if ' L ' in n:
            r = n.replace(' L ', ' R ')
            J[n] = P[n]              # replaced below
        else: J[n] = P[n]
    def chain(names):
        cur = P[names[0]].copy(); J[names[0]] = cur
        for a, b in zip(names, names[1:]):
            d = P[b] - P[a]; d2 = (P[b.replace(' L ', ' R ')] - P[a.replace(' L ', ' R ')]) * X; L = np.linalg.norm(d)
            u = d / np.linalg.norm(d) + d2 / np.linalg.norm(d2); u /= np.linalg.norm(u)
            cur = cur + u * L; J[b] = cur
    B = 'Bip02 '
    chain([B + 'L Clavicle', B + 'L UpperArm', B + 'L Forearm', B + 'L Hand'])
    chain([B + 'L Thigh', B + 'L Calf', B + 'L Foot', B + 'L Toe0'])
    return J, W, par
if __name__ == '__main__':
    J, W, par = sym()
    for k in ('Bip02 L Clavicle', 'Bip02 L UpperArm', 'Bip02 L Forearm', 'Bip02 L Hand', 'Bip02 L Thigh', 'Bip02 L Calf', 'Bip02 L Foot', 'Bip02 L Toe0'): print(k, J[k].round(3))
