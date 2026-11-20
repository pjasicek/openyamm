#!/usr/bin/env python3
"""Standing height (top of the LOD0 mesh at Standing t=0, model units) of GLBs. Args: <glb> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
from glb_pose import Glb, Model
for p in sys.argv[1:]:
    m = Model(Glb(Path(p))); X = np.vstack([q for q, _ in m.skinned_positions(m.world(m.sample('Standing', 0.0)))])
    print('HEIGHT', p, round(float(X[:, 1].max() - X[:, 1].min()), 4), 'min y', round(float(X[:, 1].min()), 4))
