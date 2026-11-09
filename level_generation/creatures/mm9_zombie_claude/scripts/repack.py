#!/usr/bin/env python3
"""New body atlas without a repaint: the torso now lives on its own part, so its charts leave the 2K body atlas; the limb charts keep their shapes and are packed again (xatlas, no new flattening). Writes work/repack.npz: uvn per body face corner.
Runs with the system python; calls claude_shared/xatlas_charts.py pack in the xatlas venv."""
import subprocess, sys
import numpy as np
F = np.load('work/faces.npz')
nb = (F['head'] == 0) & (F['torso'] == 0)
uv = F['uvb'][nb].astype(np.float32)
keys = {}
vert = np.zeros(uv.shape[:2], np.int32)
for f in range(len(uv)):
    for c in range(3):
        k = (round(float(uv[f, c, 0]), 6), round(float(uv[f, c, 1]), 6))
        vert[f, c] = keys.setdefault(k, len(keys))
np.savez('work/pack_in.npz', uv=uv, vert=vert)
print('faces', len(uv), 'uv verts', len(keys), flush=True)
subprocess.run(['../claude_shared/xatlas_venv/bin/python', '-I', '../claude_shared/xatlas_charts.py', 'pack', 'work/pack_in.npz', 'work/pack_out.npz', '--size', '2048', '--padding', '3'], check=True)
o = np.load('work/pack_out.npz')
np.savez('work/repack.npz', uvn=o['uv'], body=np.nonzero(nb)[0])
print('REPACKED', o['uv'].shape)
