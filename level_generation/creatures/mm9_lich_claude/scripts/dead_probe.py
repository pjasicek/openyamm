import sys, numpy as np, collections
from pathlib import Path
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
for f in sys.argv[1:]:
    g = Glb(Path(f)); m = Model(g)
    names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
    P = m.primitives; pr = P[0]
    w = m.world(m.sample('Dead', 0.0))
    sp = m.skinned_positions(w)
    for k in (0, 1):
        X = sp[k][0]; pr = P[k]
        o = np.argsort(X[:, 1])[:40]
        c = collections.Counter(jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in o)
        print(f, k, 'low', X[:, 1].min().round(3), c.most_common(5))
    for j in ('Bip01 Pelvis', 'Bip01 Head', 'Bip01 L Foot', 'XRobe3'):
        if j in names:
            print(j, w[names.index(j)][:3, 3].round(3))
