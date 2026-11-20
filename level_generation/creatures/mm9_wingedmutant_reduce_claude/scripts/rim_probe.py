#!/usr/bin/env python3
"""Where rim_gate.py's face/beard depth comes from: worst face/beard vertex per clip frame (rest position, dominant bone,
part) and the torso face it is inside. Usage: RIM_GLB=<glb> rim_probe.py <clip>"""
import os, sys
from pathlib import Path
import numpy as np
sys.argv = [sys.argv[0] + '_probe'] + sys.argv[1:]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rim_gate as R
clip = sys.argv[1]; dur = max(R.m.clip_times(clip)); best = (0, None)
for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 48)):
    X = np.concatenate([x for x, _ in R.m.skinned_positions(R.m.world(R.m.sample(clip, float(t))))[:len(R.P)]])
    df = R.depth(X[R.face], X)
    if df.max() > best[0]:
        i = int(df.argmax()); tf = R.torso_f[R.depth.where[i]]
        best = (float(df.max()), (k, R.X0[R.face[i]].round(3).tolist(), str(R.dom[R.face[i]]), int((df > 0.005).sum()),
                                  R.X0[R.tri[tf]].mean(0).round(3).tolist(), str(R.dom[R.tri[tf][0]])))
print('WORST', round(best[0] * 100, 2), 'cm', best[1])
