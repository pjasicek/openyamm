"""Thigh node translation per clip: min/max length, and rest, in a GLB. Args: glb..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
for p in sys.argv[1:]:
    m = Model(Glb(p)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]
    i = names.index('Bip01 R Thigh'); print(p, 'rest', np.round(doc['nodes'][i].get('translation'), 4), round(float(np.linalg.norm(doc['nodes'][i].get('translation'))), 4))
    for a in doc['animations']:
        for c in a['channels']:
            if c['target']['node'] == i and c['target']['path'] == 'translation':
                v = m.glb.accessor(a['samplers'][c['sampler']]['output'])
                l = np.linalg.norm(v, axis=1); print(f"  {a['name']:15s} len {l.min():.4f}..{l.max():.4f}  x {v[:,0].min():+.3f}..{v[:,0].max():+.3f} y {v[:,1].min():+.3f}..{v[:,1].max():+.3f} z {v[:,2].min():+.3f}..{v[:,2].max():+.3f}")
